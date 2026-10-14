import json
import math
from dataclasses import dataclass
from functools import lru_cache

from django.conf import settings
from django.core.exceptions import ValidationError

from .geometry import distance_metres
from .models import WalkableSegment


# A live point may be farther from the sparse campus graph than the ordinary
# on-path corridor, especially around the northern campus blocks.  Matches up
# to this limit are returned only as APPROACH_REQUIRED: the lateral gap is not
# added to route distance/ETA and the client labels its dashed line as an
# orientation guide, never as mapped walking geometry.  A dense boundary audit
# puts the worst current in-campus gap below 150 m; the small margin avoids a
# fragile edge cutoff without accepting the much broader 400 m context box.
MAX_NETWORK_MATCH_DISTANCE_METRES = 175
ORDINARY_NETWORK_MATCH_DISTANCE_METRES = 80
MAX_CAMPUS_BOUNDARY_UNCERTAINTY_METRES = 50
MIN_ON_PATH_CORRIDOR_METRES = 12
MAX_ON_PATH_CORRIDOR_METRES = 25
ON_PATH_ACCURACY_BUFFER_METRES = 8


@dataclass(frozen=True)
class SegmentMatch:
    segment: WalkableSegment
    coordinate: tuple[float, float]
    distance_metres: float
    leg_index: int
    leg_fraction: float
    geometry_to_start: tuple[tuple[float, float], ...]
    geometry_to_end: tuple[tuple[float, float], ...]
    distance_to_start: float
    distance_to_end: float


class LivePositionError(ValueError):
    code = "INVALID_POSITION"


class InsufficientAccuracyError(LivePositionError):
    code = "INSUFFICIENT_ACCURACY"


class NoSafeNetworkMatchError(LivePositionError):
    code = "NO_SAFE_NETWORK_MATCH"


@lru_cache(maxsize=1)
def _campus_boundary_ring():
    """Load the approved campus orientation polygon for extended matching.

    This is deliberately a read-only safety boundary, not routing geometry.
    The ordinary 80 m matcher remains available around the mapped network;
    only the wider sparse-campus approach allowance is campus constrained.
    """
    path = settings.BASE_DIR / "static/yct_map/data/yabatech-campus-boundary.geojson"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        ring = payload["features"][0]["geometry"]["coordinates"][0]
        points = tuple((float(point[0]), float(point[1])) for point in ring)
    except (OSError, ValueError, TypeError, KeyError, IndexError, json.JSONDecodeError):
        return ()
    return points if len(points) >= 4 else ()


def _point_in_ring(point, ring):
    longitude, latitude = point
    inside = False
    previous = ring[-1]
    for current in ring:
        x1, y1 = previous
        x2, y2 = current
        crosses = (y1 > latitude) != (y2 > latitude)
        if crosses and longitude < (x2 - x1) * (latitude - y1) / (y2 - y1) + x1:
            inside = not inside
        previous = current
    return inside


def _distance_to_ring(point, ring):
    return min(
        _project_to_leg(point, start, end)[2]
        for start, end in zip(ring, ring[1:])
    )


def _within_extended_campus_match_area(longitude, latitude, accuracy_metres):
    ring = _campus_boundary_ring()
    if not ring:
        return False
    point = (longitude, latitude)
    if _point_in_ring(point, ring):
        return True
    uncertainty_margin = min(
        MAX_CAMPUS_BOUNDARY_UNCERTAINTY_METRES,
        max(10, accuracy_metres + 10),
    )
    return _distance_to_ring(point, ring) <= uncertainty_margin


def validate_live_position(longitude, latitude, accuracy_metres):
    values = (longitude, latitude, accuracy_metres)
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in values):
        raise LivePositionError("Position values must be finite numbers.")
    if not -180 <= longitude <= 180 or not -90 <= latitude <= 90 or accuracy_metres < 0:
        raise LivePositionError("Position values are outside valid bounds.")
    if accuracy_metres > 40:
        raise InsufficientAccuracyError("Current location accuracy is not sufficient for routing.")
    return float(longitude), float(latitude), float(accuracy_metres)


def on_path_corridor_metres(accuracy_metres):
    """Return a conservative corridor for treating a fix as on-network.

    The browser accuracy value is an uncertainty estimate rather than a
    guarantee.  A small fixed floor avoids rejecting good fixes beside a path,
    while the cap prevents a merely acceptable (but broad) GPS uncertainty
    radius from disguising a large off-network gap.
    """
    _, _, accuracy_metres = validate_live_position(0, 0, accuracy_metres)
    return max(
        MIN_ON_PATH_CORRIDOR_METRES,
        min(MAX_ON_PATH_CORRIDOR_METRES, accuracy_metres + ON_PATH_ACCURACY_BUFFER_METRES),
    )


def _project_to_leg(point, start, end):
    longitude, latitude = point
    reference_latitude = math.radians(latitude)
    x_scale = 111_320 * max(math.cos(reference_latitude), 0.01)
    y_scale = 111_320
    ax, ay = (start[0] - longitude) * x_scale, (start[1] - latitude) * y_scale
    bx, by = (end[0] - longitude) * x_scale, (end[1] - latitude) * y_scale
    delta_x, delta_y = bx - ax, by - ay
    length_squared = delta_x * delta_x + delta_y * delta_y
    fraction = 0.0 if length_squared == 0 else max(0.0, min(1.0, -(ax * delta_x + ay * delta_y) / length_squared))
    projected = (start[0] + fraction * (end[0] - start[0]), start[1] + fraction * (end[1] - start[1]))
    return projected, fraction, math.hypot(ax + fraction * delta_x, ay + fraction * delta_y)


def _deduplicated(points):
    result = []
    for point in points:
        point = tuple(point)
        if not result or result[-1] != point:
            result.append(point)
    return tuple(result)


def _polyline_length(points):
    return sum(distance_metres(start, end) for start, end in zip(points, points[1:]))


def project_onto_segment(point, segment):
    points = [tuple(item) for item in segment.geometry["coordinates"]]
    best = None
    for index, (start, end) in enumerate(zip(points, points[1:])):
        projected, fraction, distance = _project_to_leg(point, start, end)
        candidate = (distance, index, fraction, projected)
        if best is None or candidate[:3] < best[:3]:
            best = candidate
    distance, index, fraction, projected = best
    to_start = _deduplicated([projected, *reversed(points[: index + 1])])
    to_end = _deduplicated([projected, *points[index + 1 :]])
    return SegmentMatch(
        segment=segment,
        coordinate=projected,
        distance_metres=distance,
        leg_index=index,
        leg_fraction=fraction,
        geometry_to_start=to_start,
        geometry_to_end=to_end,
        distance_to_start=_polyline_length(to_start),
        distance_to_end=_polyline_length(to_end),
    )


def _can_reach_any(match, reachable_node_ids):
    if reachable_node_ids is None:
        return True
    reachable_node_ids = {str(node_id) for node_id in reachable_node_ids}
    if str(match.segment.end_node_id) in reachable_node_ids:
        return True
    return match.segment.is_bidirectional and str(match.segment.start_node_id) in reachable_node_ids


def find_safe_network_match(longitude, latitude, accuracy_metres, *, reachable_node_ids=None):
    """Return the nearest safely matchable segment.

    When ``reachable_node_ids`` is supplied, a segment is eligible only when
    the live-origin arcs permitted by its direction can reach one of those
    nodes.  The routing service supplies the reverse-reachable set for the
    selected destination, preventing a closer disconnected component from
    stealing the live start.
    """
    longitude, latitude, accuracy_metres = validate_live_position(longitude, latitude, accuracy_metres)
    segments = WalkableSegment.objects.filter(
        is_active=True, start_node__is_active=True, end_node__is_active=True,
    ).select_related("start_node", "end_node")
    matches = [
        match
        for segment in segments
        if _can_reach_any(
            match := project_onto_segment((longitude, latitude), segment),
            reachable_node_ids,
        )
    ]
    if not matches:
        if reachable_node_ids is None:
            raise NoSafeNetworkMatchError("No active walkable network is available.")
        raise NoSafeNetworkMatchError("No active mapped path can reach the selected destination.")
    match = min(matches, key=lambda item: (item.distance_metres, str(item.segment.id)))
    if match.distance_metres > MAX_NETWORK_MATCH_DISTANCE_METRES:
        raise NoSafeNetworkMatchError("Current location cannot be safely matched to the mapped campus paths.")
    if (match.distance_metres > ORDINARY_NETWORK_MATCH_DISTANCE_METRES
            and not _within_extended_campus_match_area(longitude, latitude, accuracy_metres)):
        raise NoSafeNetworkMatchError(
            "Current location is outside the campus area supported by the extended path matcher."
        )
    return match
