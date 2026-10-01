"""Pure, conservative interpretation of immutable Path Survey evidence.

Existing graph geometry and candidate new geometry deliberately follow
different trust rules. One strong pass may corroborate geometry that existed
before the survey; a newly discovered corridor needs two independent passes.
"""

from dataclasses import dataclass
from datetime import datetime
import math
from statistics import median

from .geometry import distance_metres
from .matching import project_onto_segment


PASS_CORRIDOR_METRES = 12.0
PASS_MAX_ACCURACY_METRES = 25.0
PASS_MAX_GAP_SECONDS = 20.0
PASS_ALLOWED_GAP_SAMPLES = 1
STRONG_MIN_POINTS = 5
STRONG_MIN_COVERAGE_PERCENT = 80.0
STRONG_MAX_MEDIAN_OFFSET_METRES = 5.0
STRONG_MAX_P90_OFFSET_METRES = 9.0
STRONG_MAX_MEDIAN_ACCURACY_METRES = 8.0
STRONG_MIN_DIRECTIONAL_EFFICIENCY = 0.62
PARALLEL_AMBIGUITY_MARGIN_METRES = 2.0
DISCREPANCY_MIN_COVERAGE_PERCENT = 80.0
DISCREPANCY_MIN_MEDIAN_OFFSET_METRES = 9.0

CANDIDATE_GRAPH_CLEARANCE_METRES = 14.0
CANDIDATE_MAX_ACCURACY_METRES = 12.0
CANDIDATE_MAX_GAP_SECONDS = 20.0
CANDIDATE_MAX_STEP_METRES = 25.0
CANDIDATE_MIN_POINTS = 4
CANDIDATE_MIN_LENGTH_METRES = 15.0
CANDIDATE_MIN_DISPLACEMENT_METRES = 10.0
CANDIDATE_MATCH_ENDPOINT_METRES = 18.0
CANDIDATE_MATCH_MEAN_METRES = 10.0


@dataclass(frozen=True)
class EvidencePoint:
    coordinate: tuple[float, float]
    captured_at: datetime
    accuracy_metres: float
    sequence: int = 0


@dataclass(frozen=True)
class SegmentPass:
    points: tuple[EvidencePoint, ...]
    coverage_percent: float
    median_offset_metres: float
    p90_offset_metres: float
    median_accuracy_metres: float
    directional_efficiency: float
    mean_offset_metres: float
    conflict: bool = False

    @property
    def strong(self):
        return (
            len(self.points) >= STRONG_MIN_POINTS
            and self.coverage_percent >= STRONG_MIN_COVERAGE_PERCENT
            and self.median_offset_metres <= STRONG_MAX_MEDIAN_OFFSET_METRES
            and self.p90_offset_metres <= STRONG_MAX_P90_OFFSET_METRES
            and self.median_accuracy_metres <= STRONG_MAX_MEDIAN_ACCURACY_METRES
            and self.directional_efficiency >= STRONG_MIN_DIRECTIONAL_EFFICIENCY
            and not self.conflict
        )

    @property
    def discrepancy(self):
        """High-quality traversal consistently offset from otherwise unique geometry."""
        return (
            len(self.points) >= STRONG_MIN_POINTS
            and self.coverage_percent >= DISCREPANCY_MIN_COVERAGE_PERCENT
            and self.median_offset_metres > DISCREPANCY_MIN_MEDIAN_OFFSET_METRES
            and self.median_accuracy_metres <= STRONG_MAX_MEDIAN_ACCURACY_METRES
            and self.directional_efficiency >= STRONG_MIN_DIRECTIONAL_EFFICIENCY
            and not self.conflict
        )


def evidence_points(samples):
    return [EvidencePoint(
        coordinate=(float(sample.longitude), float(sample.latitude)),
        captured_at=sample.captured_at,
        accuracy_metres=float(sample.accuracy_metres),
        sequence=int(sample.sequence),
    ) for sample in samples]


def _percentile(values, percentile):
    if not values:
        return math.inf
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _coverage_from_projections(segment, projections):
    if len(projections) < 2 or not segment.distance_metres:
        return 0.0
    along = [projection.distance_to_start for projection in projections]
    return min(100.0, max(0.0, (max(along) - min(along)) / segment.distance_metres * 100))


def _directional_efficiency(projections):
    along = [projection.distance_to_start for projection in projections]
    travelled = sum(abs(end - start) for start, end in zip(along, along[1:]))
    return abs(along[-1] - along[0]) / travelled if travelled else 0.0


def _has_parallel_conflict(run, segment, segments):
    competitors = [item for item in segments if item.pk != segment.pk]
    if not competitors:
        return False
    ambiguous = 0
    for point, target_projection in run:
        nearest_other = min((project_onto_segment(point.coordinate, item).distance_metres
                             for item in competitors), default=math.inf)
        if nearest_other <= target_projection.distance_metres + PARALLEL_AMBIGUITY_MARGIN_METRES:
            ambiguous += 1
    return ambiguous / len(run) >= 0.35


def _build_pass(segment, run, segments):
    points = tuple(point for point, _ in run)
    projections = [projection for _, projection in run]
    offsets = [projection.distance_metres for projection in projections]
    return SegmentPass(
        points=points,
        coverage_percent=_coverage_from_projections(segment, projections),
        median_offset_metres=median(offsets),
        p90_offset_metres=_percentile(offsets, 0.9),
        median_accuracy_metres=median(point.accuracy_metres for point in points),
        directional_efficiency=_directional_efficiency(projections),
        mean_offset_metres=sum(offsets) / len(offsets),
        conflict=_has_parallel_conflict(run, segment, segments),
    )


def detect_segment_passes(points, segment, all_segments=()):
    """Return chronological corridor runs; callback density never creates passes."""
    segments = tuple(all_segments) or (segment,)
    runs = []
    current = []
    gap_count = 0
    previous_time = None

    def finish():
        nonlocal current, gap_count
        if len(current) >= 2:
            runs.append(_build_pass(segment, current, segments))
        current = []
        gap_count = 0

    for point in points:
        if previous_time is not None and (point.captured_at - previous_time).total_seconds() > PASS_MAX_GAP_SECONDS:
            finish()
        previous_time = point.captured_at
        projection = project_onto_segment(point.coordinate, segment)
        nearby = (projection.distance_metres <= PASS_CORRIDOR_METRES
                  and point.accuracy_metres <= PASS_MAX_ACCURACY_METRES)
        if nearby:
            current.append((point, projection))
            gap_count = 0
        elif current:
            gap_count += 1
            if gap_count > PASS_ALLOWED_GAP_SAMPLES:
                finish()
    finish()
    return runs


def analyse_existing_segment(points, segment, all_segments=()):
    passes = detect_segment_passes(points, segment, all_segments)
    best = max(passes, key=lambda item: (item.strong, item.coverage_percent,
                                         -item.median_offset_metres), default=None)
    if best is None:
        return {"segment": segment, "passes": (), "best": None,
                "classification": "UNOBSERVED", "auto_verify": False}
    if best.strong:
        classification = "STRONG"
    elif best.discrepancy:
        classification = "DISCREPANCY"
    elif best.conflict:
        # A nearby competing path makes attribution ambiguous; it is not by
        # itself evidence that either geometry is wrong.
        classification = "AMBIGUOUS"
    elif best.coverage_percent >= 20:
        classification = "PARTIAL"
    else:
        classification = "AMBIGUOUS"
    return {"segment": segment, "passes": tuple(passes), "best": best,
            "classification": classification, "auto_verify": best.strong}


def analyse_existing_segments(points, segments):
    segments = tuple(segments)
    return [analyse_existing_segment(points, segment, segments) for segment in segments]


def _nearest_graph_distance(point, segments):
    return min((project_onto_segment(point.coordinate, segment).distance_metres
                for segment in segments), default=math.inf)


def _trace_length(points):
    return sum(distance_metres(start.coordinate, end.coordinate) for start, end in zip(points, points[1:]))


def _simplify(points, minimum_spacing=2.0):
    kept = [points[0]]
    for point in points[1:-1]:
        if distance_metres(kept[-1].coordinate, point.coordinate) >= minimum_spacing:
            kept.append(point)
    kept.append(points[-1])
    return kept


def _candidate_run_valid(run):
    if len(run) < CANDIDATE_MIN_POINTS:
        return False
    length = _trace_length(run)
    displacement = distance_metres(run[0].coordinate, run[-1].coordinate)
    return (length >= CANDIDATE_MIN_LENGTH_METRES
            and displacement >= CANDIDATE_MIN_DISPLACEMENT_METRES
            and displacement / length >= 0.45)


def candidate_runs(points, segments):
    runs, current = [], []
    previous = None

    def finish():
        nonlocal current
        if _candidate_run_valid(current):
            runs.append(tuple(_simplify(current)))
        current = []

    for point in points:
        unexplained = (_nearest_graph_distance(point, segments) > CANDIDATE_GRAPH_CLEARANCE_METRES
                       and point.accuracy_metres <= CANDIDATE_MAX_ACCURACY_METRES)
        if not unexplained:
            if current and point.accuracy_metres <= PASS_MAX_ACCURACY_METRES:
                current.append(point)
            finish()
            previous = point
            continue
        if current:
            time_gap = (point.captured_at - current[-1].captured_at).total_seconds()
            step = distance_metres(current[-1].coordinate, point.coordinate)
            if time_gap > CANDIDATE_MAX_GAP_SECONDS or step > CANDIDATE_MAX_STEP_METRES:
                finish()
        elif previous is not None and previous.accuracy_metres <= PASS_MAX_ACCURACY_METRES:
            current.append(previous)
        current.append(point)
        previous = point
    finish()
    return runs


def _point_to_polyline_distance(point, coordinates):
    # Small local helper avoids requiring a temporary WalkableSegment object.
    latitude_scale = 111_320
    longitude_scale = latitude_scale * max(math.cos(math.radians(point[1])), 0.01)
    px, py = point[0] * longitude_scale, point[1] * latitude_scale
    best = math.inf
    for start, end in zip(coordinates, coordinates[1:]):
        ax, ay = start[0] * longitude_scale, start[1] * latitude_scale
        bx, by = end[0] * longitude_scale, end[1] * latitude_scale
        dx, dy = bx - ax, by - ay
        ratio = 0 if dx == dy == 0 else max(0, min(1, ((px-ax)*dx + (py-ay)*dy)/(dx*dx+dy*dy)))
        best = min(best, math.hypot(px-(ax+ratio*dx), py-(ay+ratio*dy)))
    return best


def _same_corridor(first, second):
    a = [point.coordinate for point in first]
    b = [point.coordinate for point in second]
    forward = max(distance_metres(a[0], b[0]), distance_metres(a[-1], b[-1]))
    reverse = max(distance_metres(a[0], b[-1]), distance_metres(a[-1], b[0]))
    if min(forward, reverse) > CANDIDATE_MATCH_ENDPOINT_METRES:
        return False
    mean_distance = sum(_point_to_polyline_distance(point, a) for point in b) / len(b)
    return mean_distance <= CANDIDATE_MATCH_MEAN_METRES


def discover_candidate_paths(points, segments):
    groups = []
    for run in candidate_runs(points, segments):
        group = next((item for item in groups if _same_corridor(item[0], run)), None)
        if group is None:
            groups.append([run])
        else:
            group.append(run)
    candidates = []
    for index, passes in enumerate(groups, 1):
        representative = max(passes, key=_trace_length)
        coordinates = [list(point.coordinate) for point in representative]
        length = _trace_length(representative)
        median_accuracy = median(point.accuracy_metres for path_pass in passes for point in path_pass)
        candidates.append({
            "id": f"C{index}",
            "geometry": {"type": "LineString", "coordinates": coordinates},
            "length_metres": round(length, 1),
            "pass_count": len(passes),
            "confirmed": len(passes) >= 2,
            "status": "Enough independent evidence" if len(passes) >= 2 else "Needs confirmation",
            "reason": ("Two independent high-quality traversals support this corridor."
                       if len(passes) >= 2 else "A second independent walk is required."),
            "median_accuracy_metres": round(median_accuracy, 1),
            "passes": tuple(passes),
        })
    return candidates
