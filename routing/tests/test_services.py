from django.test import TestCase, override_settings

from routing.models import LocationNetworkAnchor
from routing.geometry import distance_metres
from routing.results import MissingAnchorError
from routing.services import route_between_locations, route_between_nodes


class RoutingServiceTests(TestCase):
    fixtures = ["demo_locations.json", "demo_walkable_network.json", "demo_route_anchors.json"]

    def test_demo_location_anchor_fixture(self):
        self.assertEqual(LocationNetworkAnchor.objects.count(), 5)
        self.assertFalse(LocationNetworkAnchor.objects.exclude(verification_state="DEMO").exists())

    def test_route_between_locations_returns_explicit_result(self):
        anchors = list(LocationNetworkAnchor.objects.order_by("location__name")[:2])
        result = route_between_locations(anchors[0].location_id, anchors[1].location_id)
        self.assertGreater(result.distance_metres, 0)
        self.assertTrue(result.segment_ids)
        self.assertEqual(result.verification_states, ("DEMO",))

    def test_core_service_routes_nodes_without_locations(self):
        anchors = list(LocationNetworkAnchor.objects.order_by("location__name")[:2])
        result = route_between_nodes(anchors[0].node_id, anchors[1].node_id)
        self.assertGreaterEqual(len(result.node_ids), 2)

    def test_route_distance_is_arc_sum_not_endpoint_chord(self):
        anchors = list(LocationNetworkAnchor.objects.order_by("location__name")[:2])
        result = route_between_nodes(anchors[0].node_id, anchors[1].node_id)
        chord = distance_metres(result.geometry[0], result.geometry[-1])
        self.assertGreaterEqual(result.distance_metres, chord)
        self.assertAlmostEqual(result.eta_seconds, result.distance_metres / 1.35)

    def test_missing_anchor_is_explicit(self):
        anchor = LocationNetworkAnchor.objects.first()
        with self.assertRaises(MissingAnchorError):
            route_between_locations(anchor.location_id, "90000000-0000-4000-8000-000000000001")

    def test_inactive_anchor_is_rejected(self):
        anchors = list(LocationNetworkAnchor.objects.all()[:2])
        anchors[0].is_active = False
        anchors[0].save()
        with self.assertRaises(MissingAnchorError):
            route_between_locations(anchors[0].location_id, anchors[1].location_id)

    @override_settings(DEBUG=True)
    def test_debug_route_contract(self):
        anchors = list(LocationNetworkAnchor.objects.order_by("location__name")[:2])
        response = self.client.get("/api/debug/route/", {"origin": anchors[0].location_id, "destination": anchors[1].location_id})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["meta"]["route_calculated"])
        self.assertTrue(payload["meta"]["eta_is_approximate"])
        self.assertEqual(payload["route"]["properties"]["route_state"], "DEMO")

    @override_settings(DEBUG=True)
    def test_same_origin_endpoint_returns_zero_distance_point(self):
        anchor = LocationNetworkAnchor.objects.first()
        response = self.client.get("/api/debug/route/", {"origin": anchor.location_id, "destination": anchor.location_id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["route"]["geometry"]["type"], "Point")
        self.assertEqual(response.json()["route"]["properties"]["distance_metres"], 0)

    @override_settings(DEBUG=True)
    def test_debug_anchor_contract_is_small_and_demo(self):
        response = self.client.get("/api/debug/route-anchors/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["anchors"]), 5)
        self.assertEqual(set(response.json()["anchors"][0]), {"location_id", "location_name", "node_id", "verification_state"})

    @override_settings(DEBUG=False)
    def test_debug_route_endpoints_are_absent_outside_debug(self):
        self.assertEqual(self.client.get("/api/debug/route-anchors/").status_code, 404)
        self.assertEqual(self.client.get("/api/debug/route/").status_code, 404)
