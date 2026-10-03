from django.test import TestCase, override_settings

from routing.models import (LocationNetworkAnchor, SourceType, VerificationState,
                            WalkableNode, WalkableSegment)
from locations.models import Location
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

    def test_public_route_contract_excludes_graph_internals(self):
        anchors = list(LocationNetworkAnchor.objects.order_by("location__name")[:2])
        response = self.client.get("/api/routes/", {"origin": anchors[0].location_id, "destination": anchors[1].location_id})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(set(payload), {"route", "summary"})
        self.assertEqual(set(payload["route"]["properties"]), {"route_state"})
        self.assertNotIn("node_ids", str(payload))
        self.assertNotIn("segment_ids", str(payload))
        self.assertTrue(payload["summary"]["eta_is_approximate"])

    def test_public_route_same_origin_and_missing_anchor_states(self):
        anchor = LocationNetworkAnchor.objects.first()
        same = self.client.get("/api/routes/", {"origin": anchor.location_id, "destination": anchor.location_id})
        missing = self.client.get("/api/routes/", {"origin": anchor.location_id, "destination": "10000000-0000-4000-8000-000000000006"})
        self.assertEqual((same.status_code, same.json()["code"]), (409, "SAME_ORIGIN"))
        self.assertEqual((missing.status_code, missing.json()["code"]), (422, "MISSING_ANCHOR"))

    def test_distinct_destinations_at_same_arrival_node_return_explicit_state(self):
        anchor = LocationNetworkAnchor.objects.select_related("node").first()
        other = Location.objects.create(
            name="DEMO — Same arrival", category=Location.Category.BUILDING,
            publication_status=Location.PublicationStatus.PUBLISHED, is_active=True,
            representative_latitude=anchor.node.latitude,
            representative_longitude=anchor.node.longitude,
            verification_state=Location.VerificationState.DEMO,
        )
        LocationNetworkAnchor.objects.create(
            location=other, node=anchor.node, is_active=True, verification_state="DEMO"
        )
        response = self.client.get("/api/routes/", {
            "origin": anchor.location_id, "destination": other.id,
        })
        self.assertEqual((response.status_code, response.json()["code"]), (409, "ALREADY_AT_ARRIVAL"))

    def test_location_contract_identifies_only_active_anchors(self):
        response = self.client.get("/api/locations/")
        by_id = {item["properties"]["id"]: item["properties"] for item in response.json()["features"]}
        anchor = LocationNetworkAnchor.objects.first()
        self.assertTrue(by_id[str(anchor.location_id)]["routing_available"])
        anchor.is_active = False
        anchor.save()
        refreshed = self.client.get("/api/locations/").json()
        refreshed_by_id = {item["properties"]["id"]: item["properties"] for item in refreshed["features"]}
        self.assertFalse(refreshed_by_id[str(anchor.location_id)]["routing_available"])

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


class ManualShortcutRoutingRegressionTests(TestCase):
    @staticmethod
    def node(label, longitude, latitude):
        return WalkableNode.objects.create(
            label=label, longitude=longitude, latitude=latitude,
            source_type=SourceType.MANUAL,
            verification_state=VerificationState.UNVERIFIED,
        )

    @staticmethod
    def segment(start, end, *, label, active=True):
        return WalkableSegment.objects.create(
            label=label, start_node=start, end_node=end,
            geometry={"type": "LineString", "coordinates": [
                [float(start.longitude), float(start.latitude)],
                [float(end.longitude), float(end.latitude)],
            ]},
            is_bidirectional=True, is_active=active,
            source_type=SourceType.MANUAL,
            verification_state=VerificationState.UNVERIFIED,
        )

    def test_active_shortcut_is_chosen_naturally_and_never_creates_a_graph_jump(self):
        start = self.node("Start", 3.374000, 6.518000)
        detour = self.node("Detour", 3.374500, 6.518500)
        destination = self.node("Destination", 3.375000, 6.518000)
        isolated_a = self.node("Isolated A", 3.376000, 6.520000)
        isolated_b = self.node("Isolated B", 3.376100, 6.520000)
        left = self.segment(start, detour, label="Detour west")
        right = self.segment(detour, destination, label="Detour east")
        shortcut = self.segment(start, destination, label="Owner-created shortcut")
        isolated = self.segment(isolated_a, isolated_b, label="Disconnected path")

        result = route_between_nodes(start.pk, destination.pk)
        self.assertEqual(result.segment_ids, (str(shortcut.pk),))
        self.assertNotIn(str(isolated.pk), result.segment_ids)
        self.assertEqual(result.geometry[0], (float(start.longitude), float(start.latitude)))
        self.assertEqual(result.geometry[-1], (float(destination.longitude), float(destination.latitude)))
        self.assertEqual(result.verification_states, (VerificationState.UNVERIFIED,))
        self.assertAlmostEqual(result.eta_seconds, result.distance_metres / 1.35)

        shortcut.is_active = False
        shortcut.save(update_fields=("is_active",))
        detour_result = route_between_nodes(start.pk, destination.pk)
        self.assertEqual(detour_result.segment_ids, (str(left.pk), str(right.pk)))
        self.assertEqual(detour_result.node_ids, (str(start.pk), str(detour.pk), str(destination.pk)))
        self.assertGreater(detour_result.distance_metres, result.distance_metres)
