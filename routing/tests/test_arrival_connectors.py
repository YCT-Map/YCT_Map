from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from locations.models import Entrance, Floor, InternalPlace, Location
from routing.destinations import destination_summary, resolve_destination
from routing.eta import eta_seconds
from routing.models import EntranceNetworkAnchor, SourceType, VerificationState, WalkableNode, WalkableSegment
from routing.services import route_to_destination


class ArrivalConnectorRoutingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.start_node = WalkableNode.objects.create(
            label="Start node", longitude=Decimal("3.374000"), latitude=Decimal("6.518000"),
            verification_state=VerificationState.UNVERIFIED, source_type=SourceType.MANUAL,
        )
        cls.end_node = WalkableNode.objects.create(
            label="End node", longitude=Decimal("3.374500"), latitude=Decimal("6.518000"),
            verification_state=VerificationState.UNVERIFIED, source_type=SourceType.MANUAL,
        )
        cls.segment = WalkableSegment.objects.create(
            start_node=cls.start_node, end_node=cls.end_node,
            geometry={"type": "LineString", "coordinates": [[3.374, 6.518], [3.3745, 6.518]]},
            is_bidirectional=True, verification_state=VerificationState.UNVERIFIED,
            source_type=SourceType.MANUAL,
        )
        cls.origin = cls._location("TEST — Origin", "3.373900")
        cls.destination = cls._location("TEST — Building", "3.374600")
        cls.origin_entrance = cls._entrance(cls.origin, "Main Entrance", "3.373900")
        cls.destination_entrance = cls._entrance(cls.destination, "Main Entrance", "3.374600")
        cls.origin_anchor = cls._anchor(cls.origin_entrance, cls.start_node)
        cls.destination_anchor = cls._anchor(cls.destination_entrance, cls.end_node, bend=[3.37455, 6.51803])
        cls.floor = Floor.objects.create(location=cls.destination, level=1, label="First Floor", is_active=True)

    @classmethod
    def _location(cls, name, longitude):
        return Location.objects.create(
            name=name, place_type=Location.PlaceType.BUILDING,
            publication_status=Location.PublicationStatus.PUBLISHED,
            verification_state=Location.VerificationState.UNVERIFIED,
            representative_latitude=Decimal("6.518000"), representative_longitude=Decimal(longitude),
            is_active=True,
        )

    @classmethod
    def _entrance(cls, location, name, longitude, primary=True):
        return Entrance.objects.create(
            location=location, name=name, latitude=Decimal("6.518000"), longitude=Decimal(longitude),
            is_primary=primary, is_active=True, verification_state=Location.VerificationState.UNVERIFIED,
        )

    @classmethod
    def _anchor(cls, entrance, node, bend=None):
        points = [[float(node.longitude), float(node.latitude)]]
        if bend:
            points.append(bend)
        points.append([float(entrance.longitude), float(entrance.latitude)])
        anchor = EntranceNetworkAnchor(
            entrance=entrance, node=node,
            connector_geometry={"type": "LineString", "coordinates": points},
            verification_state=VerificationState.UNVERIFIED, is_active=True,
        )
        anchor.full_clean()
        anchor.save()
        return anchor

    def test_manual_route_prepends_and_appends_approved_connectors(self):
        result, _, destination = route_to_destination(self.origin.pk, f"location:{self.destination.pk}")
        self.assertEqual(result.geometry[0], (3.3739, 6.518))
        self.assertEqual(result.geometry[-1], (3.3746, 6.518))
        self.assertIn((3.37455, 6.51803), result.geometry)
        expected = (
            self.segment.distance_metres
            + self.origin_anchor.connector_distance_metres
            + self.destination_anchor.connector_distance_metres
        )
        self.assertAlmostEqual(result.distance_metres, expected, places=6)
        self.assertAlmostEqual(result.eta_seconds, eta_seconds(expected), places=6)
        self.assertTrue(destination.anchor.connector_geometry)

    def test_public_route_ends_at_physical_entrance_and_reports_connector_distance(self):
        response = self.client.get(reverse("routing:public-route"), {
            "origin": self.origin.pk, "destination": f"location:{self.destination.pk}",
        })
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["route"]["geometry"]["coordinates"][-1], [3.3746, 6.518])
        arrival = body["summary"]["destination"]["outdoor_arrival"]
        self.assertEqual(arrival["label"], "TEST — Building — Main Entrance")
        self.assertTrue(arrival["exact_connector"])
        self.assertAlmostEqual(arrival["connector_distance_metres"], round(self.destination_anchor.connector_distance_metres, 2))

    def test_legacy_anchor_without_connector_remains_functional_and_explicit(self):
        self.destination_anchor.connector_geometry = None
        self.destination_anchor.save(update_fields=("connector_geometry", "updated_at"))
        result, _, resolution = route_to_destination(self.origin.pk, self.destination.pk)
        self.assertEqual(result.geometry[-1], (3.3745, 6.518))
        self.assertTrue(resolution.routing_available)
        self.assertFalse(destination_summary(resolution)["outdoor_arrival"]["exact_connector"])

    def test_connector_validation_rejects_wrong_endpoints_and_excessive_detour(self):
        self.destination_anchor.connector_geometry = {
            "type": "LineString", "coordinates": [[6.518, 3.3745], [6.518, 3.3746]],
        }
        with self.assertRaisesMessage(ValidationError, "begin exactly at its routing node"):
            self.destination_anchor.full_clean()
        self.destination_anchor.connector_geometry = {
            "type": "LineString",
            "coordinates": [[3.3745, 6.518], [3.376, 6.519], [3.3746, 6.518]],
        }
        with self.assertRaisesMessage(ValidationError, "must remain local"):
            self.destination_anchor.full_clean()

    def test_internal_place_resolves_explicit_entrance_and_exposes_textual_handoff(self):
        side = self._entrance(self.destination, "Side Entrance", "3.374050", primary=False)
        self._anchor(side, self.start_node)
        internal = InternalPlace.objects.create(
            location=self.destination, floor=self.floor, name="Lecture Room 3",
            internal_type=InternalPlace.Type.CLASSROOM, room_code="LR3", wing_section="East Wing",
            direction_note="Take the first staircase and turn right.", routing_entrance=side,
            publication_status=Location.PublicationStatus.PUBLISHED,
            verification_state=Location.VerificationState.UNVERIFIED,
        )
        resolution = resolve_destination(f"internal:{internal.pk}", allow_legacy=False)
        self.assertEqual(resolution.entrance, side)
        summary = destination_summary(resolution)
        self.assertEqual(summary["routing_scope"], "OUTDOOR_TO_ENTRANCE")
        self.assertEqual(summary["outdoor_arrival"]["label"], "TEST — Building — Side Entrance")
        self.assertEqual(summary["indoor_handoff"], {
            "name": "Lecture Room 3", "floor": "First Floor", "room_code": "LR3",
            "wing_section": "East Wing", "direction_note": "Take the first staircase and turn right.",
        })
        route, _, routed_destination = route_to_destination(self.origin.pk, f"internal:{internal.pk}")
        self.assertEqual(route.geometry[-1], (3.37405, 6.518))
        self.assertEqual(routed_destination.destination, internal)

    def test_internal_place_without_explicit_entrance_falls_back_to_primary(self):
        internal = InternalPlace.objects.create(
            location=self.destination, floor=self.floor, name="Lecture Room 4",
            internal_type=InternalPlace.Type.CLASSROOM,
            publication_status=Location.PublicationStatus.PUBLISHED,
            verification_state=Location.VerificationState.UNVERIFIED,
        )
        resolution = resolve_destination(f"internal:{internal.pk}", allow_legacy=False)
        self.assertEqual(resolution.entrance, self.destination_entrance)
        self.assertEqual(resolution.node, self.end_node)
