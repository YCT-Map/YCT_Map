import json
from types import SimpleNamespace

from django.test import Client, SimpleTestCase, TestCase

from locations.models import Entrance
from routing.geometry import distance_metres
from routing.matching import (
    InsufficientAccuracyError,
    NoSafeNetworkMatchError,
    find_safe_network_match,
    project_onto_segment,
)
from routing.models import (
    EntranceNetworkAnchor,
    LocationNetworkAnchor,
    SourceType,
    VerificationState,
    WalkableNode,
    WalkableSegment,
)
from routing.services import (
    LIVE_ROUTE_APPROACH_REQUIRED,
    LIVE_ROUTE_ARRIVAL_CANDIDATE,
    LIVE_ROUTE_ON_NETWORK,
    route_from_live_position,
)


class ProjectionTests(SimpleTestCase):
    def test_projection_checks_every_leg_and_splits_multivertex_geometry(self):
        segment = SimpleNamespace(geometry={"type": "LineString", "coordinates": [
            [3.0, 6.0], [3.001, 6.0], [3.001, 6.001],
        ]})
        match = project_onto_segment((3.0011, 6.0006), segment)

        self.assertEqual(match.leg_index, 1)
        self.assertAlmostEqual(match.coordinate[0], 3.001, places=6)
        self.assertAlmostEqual(match.coordinate[1], 6.0006, places=6)
        self.assertEqual(match.geometry_to_start[-1], (3.0, 6.0))
        self.assertEqual(match.geometry_to_end[-1], (3.001, 6.001))
        self.assertAlmostEqual(
            match.distance_to_start,
            distance_metres(match.coordinate, (3.001, 6.0)) + distance_metres((3.001, 6.0), (3.0, 6.0)),
            places=3,
        )


class LiveRouteServiceTests(TestCase):
    fixtures = ["demo_locations.json", "demo_walkable_network.json", "demo_route_anchors.json"]

    def test_safe_match_accepts_preferred_and_strong_accuracy_caution_ranges(self):
        preferred = find_safe_network_match(3.37378, 6.51830, 35)
        caution = find_safe_network_match(3.37378, 6.51856, 20)
        self.assertLessEqual(preferred.distance_metres, 25)
        self.assertGreater(caution.distance_metres, 25)
        self.assertLessEqual(caution.distance_metres, 40)

    def test_safe_match_accepts_open_campus_area_like_sports_complex(self):
        match = find_safe_network_match(3.37425, 6.51950, 25)
        self.assertGreater(match.distance_metres, 40)
        self.assertLessEqual(match.distance_metres, 80)

    def test_safe_match_rejects_bad_accuracy_and_distant_position(self):
        with self.assertRaises(InsufficientAccuracyError):
            find_safe_network_match(3.37378, 6.51830, 41)
        with self.assertRaises(NoSafeNetworkMatchError):
            find_safe_network_match(3.3700, 6.5150, 10)

    def test_live_route_uses_ephemeral_origin_and_partial_segment_geometry(self):
        destination = LocationNetworkAnchor.objects.order_by("location__name").first()
        before_nodes = destination.node.__class__.objects.count()
        outcome = route_from_live_position(3.37378, 6.51828, 12, destination.location_id)
        result, match = outcome.result, outcome.match

        self.assertEqual(outcome.state, LIVE_ROUTE_ON_NETWORK)
        self.assertEqual(result.origin_node_id, "live-origin")
        self.assertEqual(result.geometry[0], match.coordinate)
        self.assertGreater(result.distance_metres, 0)
        self.assertEqual(destination.node.__class__.objects.count(), before_nodes)

    def test_one_way_match_only_routes_in_stored_direction(self):
        segment = WalkableSegment.objects.get(pk="20000000-0000-0000-0000-000000000001")
        segment.is_bidirectional = False
        segment.save()
        destination = LocationNetworkAnchor.objects.get(node=segment.end_node)
        outcome = route_from_live_position(3.37378, 6.51828, 12, destination.location_id)
        self.assertEqual(outcome.result.destination_node_id, str(segment.end_node_id))

    def test_destination_aware_match_skips_closer_disconnected_segment(self):
        destination = LocationNetworkAnchor.objects.get(
            node_id="10000000-0000-0000-0000-000000000003",
        )
        isolated_start = WalkableNode.objects.create(
            longitude="3.373750", latitude="6.518350",
            verification_state=VerificationState.UNVERIFIED, source_type=SourceType.MANUAL,
        )
        isolated_end = WalkableNode.objects.create(
            longitude="3.373810", latitude="6.518350",
            verification_state=VerificationState.UNVERIFIED, source_type=SourceType.MANUAL,
        )
        disconnected = WalkableSegment.objects.create(
            start_node=isolated_start, end_node=isolated_end,
            geometry={"type": "LineString", "coordinates": [[3.37375, 6.51835], [3.37381, 6.51835]]},
            is_bidirectional=True, verification_state=VerificationState.UNVERIFIED,
            source_type=SourceType.MANUAL,
        )

        outcome = route_from_live_position(3.37378, 6.51835, 8, destination.location_id)

        self.assertNotEqual(outcome.match.segment.id, disconnected.id)
        self.assertIn(str(destination.node_id), outcome.result.node_ids)
        self.assertNotIn(str(disconnected.id), outcome.result.segment_ids)

    def test_destination_aware_match_respects_one_way_direction(self):
        destination = LocationNetworkAnchor.objects.get(
            node_id="10000000-0000-0000-0000-000000000003",
        )
        reachable_start = WalkableNode.objects.get(pk="10000000-0000-0000-0000-000000000001")
        dead_end = WalkableNode.objects.create(
            longitude="3.373250", latitude="6.518100",
            verification_state=VerificationState.UNVERIFIED, source_type=SourceType.MANUAL,
        )
        wrong_way = WalkableSegment.objects.create(
            start_node=reachable_start, end_node=dead_end,
            geometry={"type": "LineString", "coordinates": [[3.3735, 6.5181], [3.37325, 6.5181]]},
            is_bidirectional=False, verification_state=VerificationState.UNVERIFIED,
            source_type=SourceType.MANUAL,
        )

        outcome = route_from_live_position(3.37330, 6.51810, 8, destination.location_id)

        self.assertNotEqual(outcome.match.segment.id, wrong_way.id)
        self.assertNotIn(str(wrong_way.id), outcome.result.segment_ids)

    def test_match_outside_accuracy_aware_corridor_requires_explicit_approach(self):
        destination = LocationNetworkAnchor.objects.get(
            node_id="10000000-0000-0000-0000-000000000003",
        )

        outcome = route_from_live_position(3.37425, 6.51950, 10, destination.location_id)

        self.assertEqual(outcome.state, LIVE_ROUTE_APPROACH_REQUIRED)
        self.assertGreater(outcome.match.distance_metres, outcome.on_path_corridor_metres)
        self.assertLessEqual(outcome.match.distance_metres, 80)
        self.assertEqual(outcome.result.geometry[0], outcome.match.coordinate)

    def test_sparse_northern_campus_area_still_returns_an_explicit_approach(self):
        destination = LocationNetworkAnchor.objects.get(
            node_id="10000000-0000-0000-0000-000000000003",
        )

        outcome = route_from_live_position(3.374700, 6.520300, 10, destination.location_id)

        self.assertEqual(outcome.state, LIVE_ROUTE_APPROACH_REQUIRED)
        self.assertGreater(outcome.match.distance_metres, 80)
        self.assertLessEqual(outcome.match.distance_metres, 175)
        self.assertEqual(outcome.result.geometry[0], outcome.match.coordinate)

    def test_extended_approach_is_rejected_outside_the_campus_boundary(self):
        destination = LocationNetworkAnchor.objects.get(
            node_id="10000000-0000-0000-0000-000000000003",
        )

        with self.assertRaises(NoSafeNetworkMatchError):
            route_from_live_position(3.374300, 6.516350, 5, destination.location_id)

    def test_physical_arrival_candidate_is_detected_before_graph_matching_without_writes(self):
        destination = LocationNetworkAnchor.objects.select_related("location", "node").first()
        entrance = Entrance.objects.create(
            location=destination.location, name="TEST — Physical entrance",
            latitude="6.519350", longitude="3.374250", is_primary=True, is_active=True,
            verification_state=destination.location.verification_state,
        )
        EntranceNetworkAnchor.objects.create(
            entrance=entrance, node=destination.node,
            connector_geometry={"type": "LineString", "coordinates": [
                [float(destination.node.longitude), float(destination.node.latitude)],
                [float(entrance.longitude), float(entrance.latitude)],
            ]},
            verification_state=VerificationState.DEMO, is_active=True,
        )
        WalkableSegment.objects.update(is_active=False)
        before = {
            "nodes": WalkableNode.objects.count(),
            "segments": WalkableSegment.objects.count(),
            "anchors": EntranceNetworkAnchor.objects.count(),
        }

        outcome = route_from_live_position(
            float(entrance.longitude), float(entrance.latitude), 5, destination.location_id,
        )

        self.assertEqual(outcome.state, LIVE_ROUTE_ARRIVAL_CANDIDATE)
        self.assertIsNone(outcome.result)
        self.assertIsNone(outcome.match)
        self.assertLess(outcome.arrival_distance_metres, 0.01)
        self.assertEqual(before, {
            "nodes": WalkableNode.objects.count(),
            "segments": WalkableSegment.objects.count(),
            "anchors": EntranceNetworkAnchor.objects.count(),
        })


class LiveRouteEndpointTests(TestCase):
    fixtures = ["demo_locations.json", "demo_walkable_network.json", "demo_route_anchors.json"]

    def setUp(self):
        self.destination = LocationNetworkAnchor.objects.order_by("location__name").first().location

    def request_payload(self, **position):
        values = {"longitude": 3.37378, "latitude": 6.51828, "accuracy_metres": 12}
        values.update(position)
        return {"destination": str(self.destination.id), "position": values}

    def test_post_contract_is_small_and_does_not_echo_raw_position(self):
        response = self.client.post(
            "/api/routes/from-position/", data=json.dumps(self.request_payload()), content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(set(payload), {"navigation_state", "route", "summary"})
        self.assertEqual(payload["navigation_state"], LIVE_ROUTE_ON_NETWORK)
        self.assertEqual(payload["summary"]["origin"], {"name": "Your location", "type": "live"})
        self.assertNotIn("node_ids", str(payload))
        self.assertNotIn("segment_ids", str(payload))
        self.assertNotIn("position", payload)
        self.assertNotIn("latitude", payload["summary"])
        self.assertNotIn("longitude", payload["summary"])

    def test_endpoint_rejects_accuracy_distance_and_invalid_coordinates(self):
        inaccurate = self.client.post("/api/routes/from-position/",
            data=json.dumps(self.request_payload(accuracy_metres=60)), content_type="application/json")
        distant = self.client.post("/api/routes/from-position/",
            data=json.dumps(self.request_payload(longitude=3.37, latitude=6.51)), content_type="application/json")
        invalid = self.client.post("/api/routes/from-position/",
            data=json.dumps(self.request_payload(longitude=181)), content_type="application/json")
        self.assertEqual((inaccurate.status_code, inaccurate.json()["code"]), (422, "INSUFFICIENT_ACCURACY"))
        self.assertEqual((distant.status_code, distant.json()["code"]), (422, "NO_SAFE_NETWORK_MATCH"))
        self.assertEqual((invalid.status_code, invalid.json()["code"]), (400, "INVALID_POSITION"))

    def test_position_at_destination_returns_arrival_candidate_before_matching(self):
        anchor = LocationNetworkAnchor.objects.select_related("node").get(location=self.destination)
        WalkableSegment.objects.update(is_active=False)
        response = self.client.post("/api/routes/from-position/", data=json.dumps({
            "destination": str(self.destination.id),
            "position": {"longitude": float(anchor.node.longitude), "latitude": float(anchor.node.latitude),
                         "accuracy_metres": 5},
        }), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["navigation_state"], LIVE_ROUTE_ARRIVAL_CANDIDATE)
        self.assertEqual(payload["summary"]["eta_label"], "Checking arrival")
        self.assertNotIn("route", payload)
        self.assertEqual(payload["summary"]["remaining_distance_metres"], 0)

    def test_approach_response_is_explicit_without_echoing_raw_position(self):
        destination = LocationNetworkAnchor.objects.get(
            node_id="10000000-0000-0000-0000-000000000003",
        ).location
        raw_position = {"longitude": 3.37425, "latitude": 6.51950, "accuracy_metres": 10}

        response = self.client.post("/api/routes/from-position/", data=json.dumps({
            "destination": str(destination.id), "position": raw_position,
        }), content_type="application/json")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["navigation_state"], LIVE_ROUTE_APPROACH_REQUIRED)
        self.assertEqual(payload["summary"]["live_start"]["state"], LIVE_ROUTE_APPROACH_REQUIRED)
        self.assertGreater(payload["summary"]["network_match_distance_metres"], 0)
        self.assertEqual(
            payload["summary"]["live_start"]["network_match_coordinate"],
            payload["route"]["geometry"]["coordinates"][0],
        )
        self.assertNotIn("latitude", str(payload))
        self.assertNotIn("longitude", str(payload))
        self.assertNotIn("position", payload)

    def test_endpoint_requires_csrf_and_does_not_accept_get(self):
        client = Client(enforce_csrf_checks=True)
        rejected = client.post("/api/routes/from-position/",
            data=json.dumps(self.request_payload()), content_type="application/json")
        self.assertEqual(rejected.status_code, 403)
        page = client.get("/")
        token = page.cookies["csrftoken"].value
        accepted = client.post("/api/routes/from-position/", data=json.dumps(self.request_payload()),
            content_type="application/json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(accepted.status_code, 200)
        self.assertEqual(client.get("/api/routes/from-position/").status_code, 405)
