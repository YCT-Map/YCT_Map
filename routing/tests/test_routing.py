from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from routing.geometry import length_metres
from routing.graph import build_graph
from routing.models import VerificationState, WalkableNode, WalkableSegment
from routing.validators import inspect_network


class RoutingFoundationTests(TestCase):
    fixtures = ["demo_walkable_network.json"]

    def test_fixture_is_explicitly_demo(self):
        self.assertEqual(WalkableNode.objects.exclude(verification_state=VerificationState.DEMO).count(), 0)
        self.assertEqual(WalkableSegment.objects.exclude(verification_state=VerificationState.DEMO).count(), 0)

    def test_curved_linestring_length_sums_every_leg(self):
        curved = {"type": "LineString", "coordinates": [[3.0, 6.0], [3.001, 6.001], [3.002, 6.0]]}
        direct = {"type": "LineString", "coordinates": [[3.0, 6.0], [3.002, 6.0]]}
        self.assertGreater(length_metres(curved), length_metres(direct))

    def test_zero_length_geometry_is_rejected(self):
        with self.assertRaises(ValidationError):
            length_metres({"type": "LineString", "coordinates": [[3, 6], [3, 6]]})

    def test_segment_rejects_self_edge(self):
        node = WalkableNode.objects.first()
        segment = WalkableSegment(start_node=node, end_node=node, geometry={"type":"LineString","coordinates":[[float(node.longitude),float(node.latitude)],[3.4,6.6]]}, verification_state="DEMO")
        with self.assertRaises(ValidationError):
            segment.full_clean()

    def test_segment_rejects_geometry_not_anchored_to_nodes(self):
        segment = WalkableSegment.objects.first()
        segment.geometry = {"type": "LineString", "coordinates": [[3.0, 6.0], [3.1, 6.1]]}
        with self.assertRaises(ValidationError):
            segment.full_clean()

    def test_graph_adds_reverse_arc_for_bidirectional_segment(self):
        graph = build_graph()
        segment = WalkableSegment.objects.first()
        self.assertTrue(any(arc.to_node_id == str(segment.end_node_id) for arc in graph.adjacency[str(segment.start_node_id)]))
        self.assertTrue(any(arc.to_node_id == str(segment.start_node_id) for arc in graph.adjacency[str(segment.end_node_id)]))

    def test_graph_ignores_inactive_segment(self):
        segment = WalkableSegment.objects.first()
        segment.is_active = False
        segment.save()
        graph = build_graph()
        self.assertFalse(any(arc.segment_id == str(segment.id) for arcs in graph.adjacency.values() for arc in arcs))

    def test_duplicate_reverse_segment_is_reported(self):
        segment = WalkableSegment.objects.first()
        duplicate = WalkableSegment(id="30000000-0000-0000-0000-000000000001", start_node=segment.end_node, end_node=segment.start_node,
            geometry={"type":"LineString","coordinates":list(reversed(segment.geometry["coordinates"]))}, is_bidirectional=True, verification_state="DEMO")
        issues = inspect_network([segment, duplicate])
        self.assertEqual(issues[0].code, "duplicate_segment")

    @override_settings(DEBUG=True)
    def test_debug_endpoint_is_explicit_and_not_a_route(self):
        response = self.client.get("/api/debug/walkable-network/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["meta"]["route_calculated"])
        self.assertTrue(all(feature["properties"]["verification_state"] == "DEMO" for feature in payload["features"]))

    @override_settings(DEBUG=False)
    def test_debug_endpoint_is_absent_outside_debug(self):
        self.assertEqual(self.client.get("/api/debug/walkable-network/").status_code, 404)
