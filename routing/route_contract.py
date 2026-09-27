import math


class InvalidRouteGeometryError(ValueError):
    """Raised when route geometry is unsafe to expose as campus GeoJSON."""


# Deliberately broader than the campus boundary. This is a last-line sanity
# guard against coordinate-order corruption, not a route or survey boundary.
YABATECH_ROUTE_BOUNDS = {
    "minimum_longitude": 3.20,
    "maximum_longitude": 3.55,
    "minimum_latitude": 6.35,
    "maximum_latitude": 6.70,
}


def validate_route_coordinates(points):
    """Return JSON-safe [longitude, latitude] pairs for a campus route."""
    if not isinstance(points, (list, tuple)) or not points:
        raise InvalidRouteGeometryError("Route geometry has no coordinates.")

    clean = []
    for point in points:
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            raise InvalidRouteGeometryError("Route coordinates must be [longitude, latitude] pairs.")
        longitude, latitude = point
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
               for value in point):
            raise InvalidRouteGeometryError("Route coordinates must be finite numbers.")
        if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
            raise InvalidRouteGeometryError("Route coordinates are outside GeoJSON bounds.")
        if not (YABATECH_ROUTE_BOUNDS["minimum_longitude"] <= longitude <=
                YABATECH_ROUTE_BOUNDS["maximum_longitude"] and
                YABATECH_ROUTE_BOUNDS["minimum_latitude"] <= latitude <=
                YABATECH_ROUTE_BOUNDS["maximum_latitude"]):
            raise InvalidRouteGeometryError(
                "Route geometry falls outside the expected YabaTech vicinity; coordinate order may be invalid."
            )
        clean.append([float(longitude), float(latitude)])
    return clean


def route_geojson_geometry(points):
    coordinates = validate_route_coordinates(points)
    if len(coordinates) == 1:
        return {"type": "Point", "coordinates": coordinates[0]}
    return {"type": "LineString", "coordinates": coordinates}
