from dataclasses import dataclass

from .geometry import length_metres
from .models import WalkableNode, WalkableSegment


@dataclass(frozen=True)
class GraphArc:
    segment_id: str
    to_node_id: str
    distance_metres: float
    geometry: tuple
    verification_state: str = ""


@dataclass(frozen=True)
class RoutingGraph:
    nodes: dict
    adjacency: dict


def build_graph():
    nodes = {str(node.id): node for node in WalkableNode.objects.filter(is_active=True)}
    adjacency = {node_id: [] for node_id in nodes}
    segments = WalkableSegment.objects.filter(is_active=True, start_node__is_active=True, end_node__is_active=True)
    for segment in segments:
        start, end = str(segment.start_node_id), str(segment.end_node_id)
        points = tuple(tuple(point) for point in segment.geometry["coordinates"])
        distance = length_metres(segment.geometry)
        adjacency[start].append(GraphArc(str(segment.id), end, distance, points, segment.verification_state))
        if segment.is_bidirectional:
            adjacency[end].append(GraphArc(str(segment.id), start, distance, tuple(reversed(points)), segment.verification_state))
    return RoutingGraph(nodes, {key: tuple(value) for key, value in adjacency.items()})
