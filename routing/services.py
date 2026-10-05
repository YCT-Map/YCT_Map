from .algorithm import find_route
from types import SimpleNamespace

from .eta import eta_seconds
from .geometry import coordinates, length_metres
from .graph import GraphArc, RoutingGraph, build_graph
from .matching import find_safe_network_match
from .models import LocationNetworkAnchor, VerificationState
from .results import MissingAnchorError, RouteResult
from .destinations import resolve_destination


def route_between_nodes(start_node_id, goal_node_id):
    return find_route(build_graph(), start_node_id, goal_node_id)


def _approved_connector(resolution):
    anchor = resolution.anchor
    if not anchor or not anchor.is_active or not anchor.connector_geometry:
        return ()
    anchor.clean()
    return tuple(coordinates(anchor.connector_geometry))


def compose_route_arrivals(result, *, origin=None, destination=None):
    """Compose approved entrance connectors around an unchanged A* graph result."""
    geometry = list(result.geometry)
    distance = result.distance_metres
    states = list(result.verification_states)

    origin_connector = _approved_connector(origin) if origin else ()
    if origin_connector:
        reversed_connector = list(reversed(origin_connector))
        geometry = reversed_connector + geometry[1:]
        distance += length_metres(origin.anchor.connector_geometry)
        states.append(origin.anchor.verification_state)

    destination_connector = _approved_connector(destination) if destination else ()
    if destination_connector:
        geometry = geometry + list(destination_connector[1:])
        distance += length_metres(destination.anchor.connector_geometry)
        states.append(destination.anchor.verification_state)

    return RouteResult(
        result.origin_node_id,
        result.destination_node_id,
        result.node_ids,
        result.segment_ids,
        tuple(geometry),
        distance,
        eta_seconds(distance),
        tuple(dict.fromkeys(states)),
    )


def route_between_locations(origin_location_id, destination_location_id):
    anchors = LocationNetworkAnchor.objects.filter(
        location_id__in=[origin_location_id, destination_location_id],
        is_active=True,
        location__publication_status="PUBLISHED",
        node__is_active=True,
    ).select_related("location", "node")
    by_location = {str(anchor.location_id): anchor for anchor in anchors}
    origin = by_location.get(str(origin_location_id))
    destination = by_location.get(str(destination_location_id))
    if not origin:
        raise MissingAnchorError("The origin has no active network anchor.")
    if not destination:
        raise MissingAnchorError("The destination has no active network anchor.")
    return find_route(build_graph(), origin.node_id, destination.node_id)


def route_to_destination(origin_location_id, destination_key):
    origin = resolve_destination(origin_location_id)
    destination = resolve_destination(destination_key)
    if not origin.routing_available:
        raise MissingAnchorError(origin.unavailable_reason)
    if not destination.routing_available:
        raise MissingAnchorError(destination.unavailable_reason)
    result = find_route(build_graph(), origin.node.id, destination.node.id)
    return compose_route_arrivals(result, origin=origin, destination=destination), origin, destination


def route_from_live_position(longitude, latitude, accuracy_metres, destination_location_id):
    destination = resolve_destination(destination_location_id)
    if not destination.routing_available:
        raise MissingAnchorError(destination.unavailable_reason)

    match = find_safe_network_match(longitude, latitude, accuracy_metres)
    graph = build_graph()
    virtual_id = "live-origin"
    nodes = dict(graph.nodes)
    nodes[virtual_id] = SimpleNamespace(
        longitude=match.coordinate[0], latitude=match.coordinate[1], verification_state=match.segment.verification_state,
    )
    adjacency = {node_id: tuple(arcs) for node_id, arcs in graph.adjacency.items()}
    arcs = []
    segment = match.segment
    if segment.is_bidirectional:
        arcs.append(GraphArc(str(segment.id), str(segment.start_node_id), match.distance_to_start,
                             match.geometry_to_start, segment.verification_state))
    arcs.append(GraphArc(str(segment.id), str(segment.end_node_id), match.distance_to_end,
                         match.geometry_to_end, segment.verification_state))
    adjacency[virtual_id] = tuple(arcs)
    result = find_route(RoutingGraph(nodes, adjacency), virtual_id, destination.node.id)
    result = compose_route_arrivals(result, destination=destination)
    return result, match, destination
