import math
from dataclasses import dataclass

from django.core.exceptions import ValidationError

from .geometry import distance_metres
from .models import WalkableSegment


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


def _validated_position(longitude, latitude, accuracy_metres):
    values = (longitude, latitude, accuracy_metres)
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in values):
        raise LivePositionError("Position values must be finite numbers.")
    if not -180 <= longitude <= 180 or not -90 <= latitude <= 90 or accuracy_metres < 0:
        raise LivePositionError("Position values are outside valid bounds.")
    if accuracy_metres > 40:
        raise InsufficientAccuracyError("Current location accuracy is not sufficient for routing.")
    return float(longitude), float(latitude), float(accuracy_metres)


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


def find_safe_network_match(longitude, latitude, accuracy_metres):
    longitude, latitude, accuracy_metres = _validated_position(longitude, latitude, accuracy_metres)
    segments = WalkableSegment.objects.filter(
        is_active=True, start_node__is_active=True, end_node__is_active=True,
    ).select_related("start_node", "end_node")
    matches = [project_onto_segment((longitude, latitude), segment) for segment in segments]
    if not matches:
        raise NoSafeNetworkMatchError("No active walkable network is available.")
    match = min(matches, key=lambda item: (item.distance_metres, str(item.segment.id)))
    if match.distance_metres > 40 or (match.distance_metres > 25 and accuracy_metres > 25):
        raise NoSafeNetworkMatchError("Current location cannot be safely matched to the mapped campus paths.")
    return match
