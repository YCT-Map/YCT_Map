"""Pure, conservative interpretation of immutable Path Survey evidence.

Existing graph geometry and candidate new geometry deliberately follow
different trust rules. Existing geometry needs cumulative independent support;
newly discovered geometry needs both explicit approval and strict independent
confirmation evidence.
"""

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
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
CUMULATIVE_MIN_INDEPENDENT_PASSES = 2
CUMULATIVE_MIN_SUPPORT_COVERAGE_PERCENT = 20.0
CUMULATIVE_MAX_GAP_PERCENT = 15.0

CANDIDATE_GRAPH_CLEARANCE_METRES = 14.0
CANDIDATE_MAX_ACCURACY_METRES = 12.0
CANDIDATE_MAX_GAP_SECONDS = 20.0
CANDIDATE_MAX_STEP_METRES = 25.0
CANDIDATE_MIN_POINTS = 4
CANDIDATE_MIN_LENGTH_METRES = 15.0
CANDIDATE_MIN_DISPLACEMENT_METRES = 10.0
CANDIDATE_MATCH_ENDPOINT_METRES = 10.0
CANDIDATE_MATCH_MEAN_METRES = 4.0
CANDIDATE_MAX_UNAMBIGUOUS_MEAN_METRES = 2.0


@dataclass(frozen=True)
class EvidencePoint:
    coordinate: tuple[float, float]
    captured_at: datetime
    accuracy_metres: float
    sequence: int = 0
    survey_id: object | None = None


@dataclass(frozen=True)
class SegmentPass:
    points: tuple[EvidencePoint, ...]
    coverage_percent: float
    median_offset_metres: float
    p90_offset_metres: float
    median_accuracy_metres: float
    directional_efficiency: float
    mean_offset_metres: float
    start_distance_metres: float
    end_distance_metres: float
    survey_id: object | None = None
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

    @property
    def supporting(self):
        """Whether this pass is trustworthy corroboration, even if incomplete."""
        return (
            len(self.points) >= STRONG_MIN_POINTS
            and self.coverage_percent >= CUMULATIVE_MIN_SUPPORT_COVERAGE_PERCENT
            and self.median_offset_metres <= STRONG_MAX_MEDIAN_OFFSET_METRES
            and self.p90_offset_metres <= STRONG_MAX_P90_OFFSET_METRES
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
        survey_id=getattr(sample, "survey_id", None),
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
        # If the reported uncertainty could plausibly place the observation on
        # either path, attribution is ambiguous even when the target is a few
        # metres closer. This deliberately favours human review on close
        # parallel campus paths.
        uncertainty_margin = max(
            PARALLEL_AMBIGUITY_MARGIN_METRES,
            min(10.0, point.accuracy_metres),
        )
        if nearest_other <= target_projection.distance_metres + uncertainty_margin:
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
        start_distance_metres=min(projection.distance_to_start for projection in projections),
        end_distance_metres=max(projection.distance_to_start for projection in projections),
        survey_id=points[0].survey_id,
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


def _merged_interval_coverage(segment, passes):
    """Return union coverage and largest unsupported gap between supporting runs."""
    if not passes or not segment.distance_metres:
        return 0.0, math.inf
    intervals = sorted(
        (max(0.0, item.start_distance_metres),
         min(segment.distance_metres, item.end_distance_metres))
        for item in passes
    )
    merged = []
    for start, end in intervals:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    covered = sum(end - start for start, end in merged)
    gaps = [end[0] - start[1] for start, end in zip(merged, merged[1:])]
    return min(100.0, covered / segment.distance_metres * 100), max(gaps, default=0.0)


def analyse_cumulative_existing_segment(point_sets, segment, all_segments=()):
    """Combine finalized evidence as independent runs, never as one synthetic trace."""
    passes = tuple(
        segment_pass
        for points in point_sets
        for segment_pass in detect_segment_passes(points, segment, all_segments)
    )
    best = max(
        passes,
        key=lambda item: (item.strong, item.supporting, item.coverage_percent,
                          -item.median_offset_metres),
        default=None,
    )
    if best is None:
        return {
            "segment": segment, "passes": (), "supporting_passes": (), "best": None,
            "classification": "UNOBSERVED", "auto_verify": False,
            "evidence_sufficient": False, "needs_confirmation": False,
            "needs_review": False,
            "cumulative_coverage_percent": 0.0,
        }

    supporting = tuple(item for item in passes if item.supporting)
    cumulative_coverage, largest_gap = _merged_interval_coverage(segment, supporting)
    max_gap = max(8.0, segment.distance_metres * CUMULATIVE_MAX_GAP_PERCENT / 100)
    contradictions = tuple(item for item in passes if item.conflict or item.discrepancy)
    independently_supported = len(supporting) >= CUMULATIVE_MIN_INDEPENDENT_PASSES
    evidence_sufficient = (
        independently_supported
        and cumulative_coverage >= STRONG_MIN_COVERAGE_PERCENT
        and largest_gap <= max_gap
        and not contradictions
    )
    if evidence_sufficient:
        classification = "STRONG"
    elif any(item.discrepancy for item in passes):
        classification = "DISCREPANCY"
    elif any(item.conflict for item in passes):
        classification = "AMBIGUOUS"
    elif supporting:
        classification = "STRONG" if any(item.strong for item in supporting) else "PARTIAL"
    elif best.coverage_percent >= 20:
        classification = "PARTIAL"
    else:
        classification = "AMBIGUOUS"
    return {
        "segment": segment,
        "passes": passes,
        "supporting_passes": supporting,
        "best": best,
        "classification": classification,
        "auto_verify": evidence_sufficient,
        "evidence_sufficient": evidence_sufficient,
        "needs_confirmation": not evidence_sufficient and classification != "UNOBSERVED",
        "needs_review": bool(contradictions),
        "cumulative_coverage_percent": cumulative_coverage,
    }


def analyse_cumulative_existing_segments(point_sets, segments):
    segments = tuple(segments)
    point_sets = tuple(tuple(points) for points in point_sets)
    return [analyse_cumulative_existing_segment(point_sets, segment, segments)
            for segment in segments]


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


def _project_to_polyline(point, coordinates):
    """Return local-metre offset and along-distance for candidate evidence."""
    latitude_scale = 111_320
    longitude_scale = latitude_scale * max(math.cos(math.radians(point[1])), 0.01)
    px, py = point[0] * longitude_scale, point[1] * latitude_scale
    best = (math.inf, 0.0)
    cumulative = 0.0
    for start, end in zip(coordinates, coordinates[1:]):
        ax, ay = start[0] * longitude_scale, start[1] * latitude_scale
        bx, by = end[0] * longitude_scale, end[1] * latitude_scale
        dx, dy = bx - ax, by - ay
        leg = math.hypot(dx, dy)
        ratio = 0 if leg == 0 else max(0, min(1, ((px-ax)*dx + (py-ay)*dy)/(leg*leg)))
        candidate = (math.hypot(px-(ax+ratio*dx), py-(ay+ratio*dy)), cumulative + ratio*leg)
        if candidate[0] < best[0]:
            best = candidate
        cumulative += leg
    return best, cumulative


def _candidate_pass_metrics(run, representative):
    coordinates = [point.coordinate for point in representative]
    projections = [_project_to_polyline(point.coordinate, coordinates)[0] for point in run]
    offsets = [item[0] for item in projections]
    total = _project_to_polyline(run[-1].coordinate, coordinates)[1]
    coverage = ((max(item[1] for item in projections) - min(item[1] for item in projections)) /
                total * 100 if total else 0.0)
    return {
        "point_count": len(run),
        "coverage_percent": coverage,
        "median_offset_metres": median(offsets),
        "p90_offset_metres": _percentile(offsets, 0.9),
        "median_accuracy_metres": median(point.accuracy_metres for point in run),
        "directional_efficiency": (
            distance_metres(run[0].coordinate, run[-1].coordinate) / _trace_length(run)
            if _trace_length(run) else 0.0
        ),
    }


def _candidate_pass_supports_verification(run, representative):
    metrics = _candidate_pass_metrics(run, representative)
    return (
        metrics["point_count"] >= STRONG_MIN_POINTS
        and metrics["coverage_percent"] >= STRONG_MIN_COVERAGE_PERCENT
        and metrics["median_offset_metres"] <= STRONG_MAX_MEDIAN_OFFSET_METRES
        and metrics["p90_offset_metres"] <= STRONG_MAX_P90_OFFSET_METRES
        and metrics["median_accuracy_metres"] <= STRONG_MAX_MEDIAN_ACCURACY_METRES
        and metrics["directional_efficiency"] >= STRONG_MIN_DIRECTIONAL_EFFICIENCY
    )


def candidate_has_strict_confirmation(candidate):
    """Recheck strict pass evidence instead of trusting a caller-supplied flag."""
    passes = tuple(candidate.get("passes") or ())
    if len(passes) < CUMULATIVE_MIN_INDEPENDENT_PASSES:
        return False
    representative = max(passes, key=_trace_length)
    return sum(
        _candidate_pass_supports_verification(path_pass, representative)
        for path_pass in passes
    ) >= CUMULATIVE_MIN_INDEPENDENT_PASSES


def candidate_fingerprint(geometry):
    coordinates = [[round(float(value), 6) for value in point]
                   for point in geometry["coordinates"]]
    reverse = list(reversed(coordinates))
    canonical = min(coordinates, reverse)
    return hashlib.sha256(json.dumps(canonical, separators=(",", ":")).encode()).hexdigest()


def candidate_confirmation_token(candidate):
    """Bind approval to both proposed geometry and the evidence behind its state."""
    passes = tuple(candidate.get("passes") or ())
    evidence = []
    for path_pass in passes:
        if not path_pass:
            continue
        evidence.append({
            "survey_id": str(path_pass[0].survey_id or ""),
            "started_at": path_pass[0].captured_at.isoformat(),
            "ended_at": path_pass[-1].captured_at.isoformat(),
            "sequences": [point.sequence for point in path_pass],
            "coordinates": [
                [round(float(value), 6) for value in point.coordinate]
                for point in path_pass
            ],
            "accuracies": [round(float(point.accuracy_metres), 2) for point in path_pass],
        })
    payload = {
        "geometry": candidate.get("fingerprint") or candidate_fingerprint(candidate["geometry"]),
        "verification_ready": candidate_has_strict_confirmation(candidate),
        "evidence": evidence,
    }
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"),
    ).encode()).hexdigest()


def _candidate_unambiguous_mean_metres(first, second):
    """Require close agreement when uncertainty could conceal parallel paths."""
    median_accuracy = min(
        median(point.accuracy_metres for point in first),
        median(point.accuracy_metres for point in second),
    )
    return min(
        CANDIDATE_MAX_UNAMBIGUOUS_MEAN_METRES,
        max(0.75, median_accuracy * 0.4),
    )


def _same_corridor(first, second):
    a = [point.coordinate for point in first]
    b = [point.coordinate for point in second]
    forward = max(distance_metres(a[0], b[0]), distance_metres(a[-1], b[-1]))
    reverse = max(distance_metres(a[0], b[-1]), distance_metres(a[-1], b[0]))
    if min(forward, reverse) > CANDIDATE_MATCH_ENDPOINT_METRES:
        return False
    forward_mean = sum(_point_to_polyline_distance(point, a) for point in b) / len(b)
    reverse_mean = sum(_point_to_polyline_distance(point, b) for point in a) / len(a)
    mean_separation = max(forward_mean, reverse_mean)
    if mean_separation > CANDIDATE_MATCH_MEAN_METRES:
        return False
    # Close-but-distinct candidate traces are not safe automatic confirmation:
    # the reported uncertainty could conceal two genuinely parallel paths.
    return mean_separation <= _candidate_unambiguous_mean_metres(first, second)


def _candidate_from_passes(index, passes):
    representative = max(passes, key=_trace_length)
    coordinates = [list(point.coordinate) for point in representative]
    geometry = {"type": "LineString", "coordinates": coordinates}
    length = _trace_length(representative)
    median_accuracy = median(point.accuracy_metres for path_pass in passes for point in path_pass)
    qualifying = tuple(path_pass for path_pass in passes
                       if _candidate_pass_supports_verification(path_pass, representative))
    confirmed = len(qualifying) >= CUMULATIVE_MIN_INDEPENDENT_PASSES
    return {
        "id": f"C{index}",
        "fingerprint": candidate_fingerprint(geometry),
        "geometry": geometry,
        "length_metres": round(length, 1),
        "pass_count": len(passes),
        "qualifying_pass_count": len(qualifying),
        "confirmed": confirmed,
        "verification_ready": confirmed,
        "status": "Enough strict independent evidence" if confirmed else "Needs confirmation",
        "reason": (
            "At least two independent traversals meet the strict verification thresholds."
            if confirmed else
            "Another independent high-quality walk is required before verification."
        ),
        "median_accuracy_metres": round(median_accuracy, 1),
        "passes": tuple(passes),
    }


def discover_candidate_paths(points, segments):
    groups = []
    for run in candidate_runs(points, segments):
        group = next((item for item in groups if _same_corridor(item[0], run)), None)
        if group is None:
            groups.append([run])
        else:
            group.append(run)
    return [_candidate_from_passes(index, passes) for index, passes in enumerate(groups, 1)]


def discover_cumulative_candidate_paths(point_sets, segments):
    """Group geometrically matching candidate runs without joining survey traces."""
    groups = []
    for points in point_sets:
        for run in candidate_runs(points, segments):
            group = next((item for item in groups if _same_corridor(item[0], run)), None)
            if group is None:
                groups.append([run])
            else:
                group.append(run)
    groups.sort(key=lambda group: (
        round(group[0][0].coordinate[0], 6),
        round(group[0][0].coordinate[1], 6),
        round(group[0][-1].coordinate[0], 6),
        round(group[0][-1].coordinate[1], 6),
    ))
    return [_candidate_from_passes(index, passes) for index, passes in enumerate(groups, 1)]
