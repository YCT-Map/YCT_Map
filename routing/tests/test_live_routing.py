import json
from types import SimpleNamespace

from django.test import Client, SimpleTestCase, TestCase

from routing.geometry import distance_metres
from routing.matching import (
    InsufficientAccuracyError,
    NoSafeNetworkMatchError,
    find_safe_network_match,
    project_onto_segment,
)
from routing.models import LocationNetworkAnchor, WalkableSegment
from routing.services import route_from_live_position


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

    def test_safe_match_rejects_bad_accuracy_and_distant_position(self):
        with self.assertRaises(InsufficientAccuracyError):
            find_safe_network_match(3.37378, 6.51830, 41)
        with self.assertRaises(NoSafeNetworkMatchError):
            find_safe_network_match(3.3700, 6.5150, 10)

    def test_live_route_uses_ephemeral_origin_and_partial_segment_geometry(self):
        destination = LocationNetworkAnchor.objects.order_by("location__name").first()
        before_nodes = destination.node.__class__.objects.count()
        result, match, _ = route_from_live_position(3.37378, 6.51828, 12, destination.location_id)

        self.assertEqual(result.origin_node_id, "live-origin")
        self.assertEqual(result.geometry[0], match.coordinate)
        self.assertGreater(result.distance_metres, 0)
        self.assertEqual(destination.node.__class__.objects.count(), before_nodes)

    def test_one_way_match_only_routes_in_stored_direction(self):
        segment = WalkableSegment.objects.get(pk="20000000-0000-0000-0000-000000000001")
        segment.is_bidirectional = False
        segment.save()
        destination = LocationNetworkAnchor.objects.get(node=segment.end_node)
        result, _, _ = route_from_live_position(3.37378, 6.51828, 12, destination.location_id)
        self.assertEqual(result.destination_node_id, str(segment.end_node_id))


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
        self.assertEqual(set(payload), {"route", "summary"})
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

    def test_position_at_destination_arrival_returns_explicit_state_not_unrenderable_point(self):
        anchor = LocationNetworkAnchor.objects.select_related("node").get(location=self.destination)
        response = self.client.post("/api/routes/from-position/", data=json.dumps({
            "destination": str(self.destination.id),
            "position": {"longitude": float(anchor.node.longitude), "latitude": float(anchor.node.latitude),
                         "accuracy_metres": 5},
        }), content_type="application/json")
        self.assertEqual((response.status_code, response.json()["code"]), (409, "ALREADY_AT_ARRIVAL"))

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
