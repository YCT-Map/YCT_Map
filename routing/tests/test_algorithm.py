from types import SimpleNamespace

from django.test import SimpleTestCase

from routing.algorithm import find_route
from routing.eta import eta_seconds, format_approximate_eta
from routing.graph import GraphArc, RoutingGraph
from routing.results import InvalidNodeError, NoRouteError, RoutingError
from routing.route_geometry import assemble_route_geometry


def node(state="DEMO"):
    return SimpleNamespace(longitude=3.0, latitude=6.0, verification_state=state)


def arc(segment, destination, cost, points):
    return GraphArc(segment, destination, cost, tuple(points))


class AStarTests(SimpleTestCase):
    def test_direct_route(self):
        graph = RoutingGraph({"A": node(), "B": node()}, {"A": (arc("AB", "B", 10, ((0, 0), (1, 0))),), "B": ()})
        result = find_route(graph, "A", "B")
        self.assertEqual(result.node_ids, ("A", "B"))
        self.assertEqual(result.segment_ids, ("AB",))
        self.assertEqual(result.distance_metres, 10)

    def test_lower_distance_wins_over_fewer_hops(self):
        graph = RoutingGraph(
            {name: node() for name in "ABCD"},
            {
                "A": (arc("AD", "D", 250, ((0, 0), (3, 0))), arc("AB", "B", 60, ((0, 0), (1, 0)))),
                "B": (arc("BC", "C", 60, ((1, 0), (2, 0))),),
                "C": (arc("CD", "D", 60, ((2, 0), (3, 0))),),
                "D": (),
            },
        )
        result = find_route(graph, "A", "D")
        self.assertEqual(result.segment_ids, ("AB", "BC", "CD"))
        self.assertEqual(result.distance_metres, 180)

    def test_route_reconstruction_deduplicates_junctions_and_retains_vertices(self):
        graph = RoutingGraph(
            {name: node() for name in "ABC"},
            {
                "A": (arc("AB", "B", 10, ((0, 0), (0.5, 0.2), (1, 0))),),
                "B": (arc("BC", "C", 20, ((1, 0), (1.5, 0.3), (2, 0))),),
                "C": (),
            },
        )
        result = find_route(graph, "A", "C")
        self.assertEqual(result.geometry, ((0, 0), (0.5, 0.2), (1, 0), (1.5, 0.3), (2, 0)))

    def test_unreachable_route(self):
        graph = RoutingGraph({"A": node(), "B": node()}, {"A": (), "B": ()})
        with self.assertRaises(NoRouteError):
            find_route(graph, "A", "B")

    def test_same_origin_is_zero_distance(self):
        graph = RoutingGraph({"A": node()}, {"A": ()})
        result = find_route(graph, "A", "A")
        self.assertEqual(result.node_ids, ("A",))
        self.assertEqual(result.segment_ids, ())
        self.assertEqual(result.distance_metres, 0)
        self.assertEqual(result.eta_seconds, 0)

    def test_one_way_route_exists_only_in_allowed_direction(self):
        graph = RoutingGraph({"A": node(), "B": node()}, {"A": (arc("AB", "B", 10, ((0, 0), (1, 0))),), "B": ()})
        self.assertEqual(find_route(graph, "A", "B").segment_ids, ("AB",))
        with self.assertRaises(NoRouteError):
            find_route(graph, "B", "A")

    def test_unknown_or_inactive_node_is_rejected(self):
        graph = RoutingGraph({"A": node()}, {"A": ()})
        with self.assertRaises(InvalidNodeError):
            find_route(graph, "A", "retired")

    def test_equal_cost_route_is_deterministic_by_stable_node_id(self):
        graph = RoutingGraph(
            {name: node() for name in "ABCD"},
            {
                "A": (arc("AC", "C", 10, ((0, 0), (1, 1))), arc("AB", "B", 10, ((0, 0), (1, -1)))),
                "B": (arc("BD", "D", 10, ((1, -1), (2, 0))),),
                "C": (arc("CD", "D", 10, ((1, 1), (2, 0))),),
                "D": (),
            },
        )
        self.assertEqual(find_route(graph, "A", "D").segment_ids, ("AB", "BD"))


class GeometryAndEtaTests(SimpleTestCase):
    def test_reverse_arc_geometry_is_preserved(self):
        reverse = arc("AB", "A", 10, ((2, 0), (1, 0.5), (0, 0)))
        self.assertEqual(assemble_route_geometry((reverse,)), reverse.geometry)

    def test_discontinuous_geometry_is_rejected(self):
        arcs = (arc("AB", "B", 10, ((0, 0), (1, 0))), arc("BC", "C", 10, ((2, 0), (3, 0))))
        with self.assertRaises(RoutingError):
            assemble_route_geometry(arcs)

    def test_baseline_eta_and_approximate_format(self):
        self.assertAlmostEqual(eta_seconds(81), 60)
        self.assertEqual(format_approximate_eta(60), "~1 min")
        self.assertEqual(format_approximate_eta(61), "~2 min")
        self.assertEqual(format_approximate_eta(0), "0 min")
