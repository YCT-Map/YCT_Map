import math

from django.core.exceptions import ValidationError

EARTH_RADIUS_METRES = 6_371_008.8


def coordinates(geometry):
    if not isinstance(geometry, dict) or geometry.get("type") != "LineString":
        raise ValidationError("Geometry must be a GeoJSON LineString.")
    points = geometry.get("coordinates")
    if not isinstance(points, list) or len(points) < 2:
        raise ValidationError("A segment needs at least two coordinates.")
    clean = []
    for point in points:
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            raise ValidationError("Each coordinate must be [longitude, latitude].")
        longitude, latitude = point
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in point):
            raise ValidationError("Coordinates must contain finite numbers.")
        if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
            raise ValidationError("A coordinate is outside longitude/latitude bounds.")
        clean.append((float(longitude), float(latitude)))
    return clean


def distance_metres(start, end):
    lon1, lat1 = map(math.radians, start)
    lon2, lat2 = map(math.radians, end)
    delta_lat, delta_lon = lat2 - lat1, lon2 - lon1
    value = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    return EARTH_RADIUS_METRES * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def length_metres(geometry):
    points = coordinates(geometry)
    total = sum(distance_metres(start, end) for start, end in zip(points, points[1:]))
    if total <= 0:
        raise ValidationError("A segment must have a positive geometry-derived length.")
    return total
