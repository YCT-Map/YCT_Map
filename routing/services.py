from .algorithm import find_route
from .graph import build_graph
from .models import LocationNetworkAnchor
from .results import MissingAnchorError


def route_between_nodes(start_node_id, goal_node_id):
    return find_route(build_graph(), start_node_id, goal_node_id)


def route_between_locations(origin_location_id, destination_location_id):
    anchors = LocationNetworkAnchor.objects.filter(
        location_id__in=[origin_location_id, destination_location_id],
        is_active=True,
        location__is_active=True,
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
