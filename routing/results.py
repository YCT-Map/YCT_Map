from dataclasses import dataclass


class RoutingError(Exception):
    """Base class for expected route-calculation failures."""


class InvalidNodeError(RoutingError):
    pass


class NoRouteError(RoutingError):
    pass


class MissingAnchorError(RoutingError):
    pass


@dataclass(frozen=True)
class RouteResult:
    origin_node_id: str
    destination_node_id: str
    node_ids: tuple[str, ...]
    segment_ids: tuple[str, ...]
    geometry: tuple[tuple[float, float], ...]
    distance_metres: float
    eta_seconds: float
    verification_states: tuple[str, ...]
