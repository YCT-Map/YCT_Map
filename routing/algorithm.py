import heapq
import math

from .eta import eta_seconds
from .geometry import distance_metres
from .route_geometry import assemble_route_geometry
from .results import InvalidNodeError, NoRouteError, RouteResult


def _node_coordinate(node):
    return float(node.longitude), float(node.latitude)


def find_route(graph, start_node_id, goal_node_id):
    """Find the lowest-distance route with an admissible Haversine heuristic."""
    start, goal = str(start_node_id), str(goal_node_id)
    if start not in graph.nodes:
        raise InvalidNodeError(f"Unknown or inactive start node: {start}")
    if goal not in graph.nodes:
        raise InvalidNodeError(f"Unknown or inactive destination node: {goal}")
    if start == goal:
        coordinate = _node_coordinate(graph.nodes[start])
        state = getattr(graph.nodes[start], "verification_state", "")
        return RouteResult(start, goal, (start,), (), (coordinate,), 0.0, 0.0, (state,))

    goal_coordinate = _node_coordinate(graph.nodes[goal])
    g_scores = {start: 0.0}
    predecessors = {}
    queue = [(distance_metres(_node_coordinate(graph.nodes[start]), goal_coordinate), 0.0, start)]

    while queue:
        _, queued_cost, node_id = heapq.heappop(queue)
        if not math.isclose(queued_cost, g_scores.get(node_id, math.inf), abs_tol=1e-9):
            continue
        if node_id == goal:
            break
        for arc in sorted(graph.adjacency.get(node_id, ()), key=lambda item: (item.to_node_id, item.segment_id)):
            candidate_cost = queued_cost + arc.distance_metres
            known_cost = g_scores.get(arc.to_node_id, math.inf)
            if candidate_cost + 1e-9 < known_cost:
                g_scores[arc.to_node_id] = candidate_cost
                predecessors[arc.to_node_id] = (node_id, arc)
                heuristic = distance_metres(_node_coordinate(graph.nodes[arc.to_node_id]), goal_coordinate)
                heapq.heappush(queue, (candidate_cost + heuristic, candidate_cost, arc.to_node_id))

    if goal not in predecessors:
        raise NoRouteError(f"No walkable route exists from {start} to {goal}.")

    nodes_reversed, arcs_reversed = [goal], []
    current = goal
    while current != start:
        previous, arc = predecessors[current]
        arcs_reversed.append(arc)
        nodes_reversed.append(previous)
        current = previous
    node_ids = tuple(reversed(nodes_reversed))
    arcs = tuple(reversed(arcs_reversed))
    distance = sum(arc.distance_metres for arc in arcs)
    states = tuple(dict.fromkeys(
        [getattr(graph.nodes[node_id], "verification_state", "") for node_id in node_ids]
        + [arc.verification_state for arc in arcs]
    ))
    return RouteResult(
        start,
        goal,
        node_ids,
        tuple(arc.segment_id for arc in arcs),
        assemble_route_geometry(arcs),
        distance,
        eta_seconds(distance),
        states,
    )
