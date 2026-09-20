from .algorithm import find_route
from types import SimpleNamespace

from .graph import GraphArc, RoutingGraph, build_graph
from .matching import find_safe_network_match
from .models import LocationNetworkAnchor, VerificationState
from .results import MissingAnchorError


def route_between_nodes(start_node_id, goal_node_id):
    return find_route(build_graph(), start_node_id, goal_node_id)


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


def route_from_live_position(longitude, latitude, accuracy_metres, destination_location_id):
    destination = LocationNetworkAnchor.objects.filter(
        location_id=destination_location_id,
        is_active=True,
        location__publication_status="PUBLISHED",
        node__is_active=True,
    ).select_related("location", "node").first()
    if not destination:
        raise MissingAnchorError("The destination has no active network anchor.")

    match = find_safe_network_match(longitude, latitude, accuracy_metres)
    graph = build_graph()
    virtual_id = "live-origin"
    nodes = dict(graph.nodes)
    nodes[virtual_id] = SimpleNamespace(
        longitude=match.coordinate[0], latitude=match.coordinate[1], verification_state=VerificationState.UNVERIFIED,
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
    result = find_route(RoutingGraph(nodes, adjacency), virtual_id, destination.node_id)
    return result, match, destination.location
