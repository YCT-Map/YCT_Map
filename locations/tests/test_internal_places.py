from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from locations.models import Entrance, Floor, InternalPlace, Location
from routing.models import EntranceNetworkAnchor, VerificationState, WalkableNode


class InternalDestinationTests(TestCase):
    def setUp(self):
        self.location = Location.objects.create(
            name="Published Building", category=Location.Category.BUILDING,
            place_type=Location.PlaceType.BUILDING,
            publication_status=Location.PublicationStatus.PUBLISHED, is_active=True,
            representative_latitude=Decimal("6.518500"), representative_longitude=Decimal("3.374200"),
        )
        self.floor = Floor.objects.create(location=self.location, level=0, label="Ground Floor")

    def test_published_place_remains_public_without_routing(self):
        response = self.client.get(reverse("locations:collection"))
        feature = response.json()["features"][0]["properties"]
        self.assertFalse(feature["routing_available"])
        self.assertIn("primary entrance", feature["routing_unavailable_reason"])

    def test_published_internal_place_is_searchable_without_routing(self):
        place = InternalPlace.objects.create(
            location=self.location, floor=self.floor, name="Room G1", internal_type=InternalPlace.Type.CLASSROOM,
            publication_status=Location.PublicationStatus.PUBLISHED,
        )
        response = self.client.get(reverse("locations:search"), {"q": "G1"})
        result = next(item for item in response.json()["results"] if item["id"] == str(place.id))
        self.assertFalse(result["routing_available"])
        self.assertEqual(result["destination_key"], f"internal:{place.id}")

    def test_active_primary_is_unique(self):
        Entrance.objects.create(location=self.location, name="Main", latitude=Decimal("6.5185"),
                                longitude=Decimal("3.3742"), is_primary=True)
        with self.assertRaises(Exception):
            Entrance.objects.create(location=self.location, name="Side", latitude=Decimal("6.5186"),
                                    longitude=Decimal("3.3743"), is_primary=True)

    def test_cross_parent_floor_and_entrance_are_rejected(self):
        other = Location.objects.create(name="Other")
        other_floor = Floor.objects.create(location=other, level=0, label="Ground")
        other_entrance = Entrance.objects.create(location=other, name="Main", latitude=Decimal("6.5"), longitude=Decimal("3.3"))
        place = InternalPlace(location=self.location, floor=other_floor, routing_entrance=other_entrance,
                              name="Wrong", internal_type=InternalPlace.Type.OFFICE)
        with self.assertRaises(ValidationError):
            place.full_clean()

    def test_entrance_anchor_enables_directions(self):
        entrance = Entrance.objects.create(location=self.location, name="Main", latitude=Decimal("6.5185"),
                                            longitude=Decimal("3.3742"), is_primary=True)
        node = WalkableNode.objects.create(longitude=Decimal("3.3742"), latitude=Decimal("6.5185"),
                                           verification_state=VerificationState.UNVERIFIED)
        EntranceNetworkAnchor.objects.create(entrance=entrance, node=node, verification_state=VerificationState.UNVERIFIED)
        feature = self.client.get(reverse("locations:collection")).json()["features"][0]["properties"]
        self.assertTrue(feature["routing_available"])
        self.assertEqual(feature["routing_unavailable_reason"], "")

    def test_directory_groups_places_by_floor(self):
        InternalPlace.objects.create(location=self.location, floor=self.floor, name="Lab",
                                     internal_type=InternalPlace.Type.LABORATORY,
                                     publication_status=Location.PublicationStatus.PUBLISHED)
        response = self.client.get(reverse("locations:internal-directory", args=[self.location.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["floors"][0]["label"], "Ground Floor")
