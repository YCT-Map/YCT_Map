from decimal import Decimal
import json
from django.test import Client, TestCase
from django.urls import reverse

from locations.models import Entrance, Location
from routing.models import (
    EntranceNetworkAnchor,
    VerificationState,
    WalkableNode,
    WalkableSegment,
)


class RouteVerificationEndpointTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create two published locations with active entrances
        self.loc_a = Location.objects.create(
            name="Alpha Building",
            category="building",
            publication_status=Location.PublicationStatus.PUBLISHED,
            verification_state=VerificationState.FIELD_VERIFIED,
            representative_latitude=Decimal("6.5180"),
            representative_longitude=Decimal("3.3740"),
        )
        self.loc_b = Location.objects.create(
            name="Beta Building",
            category="building",
            publication_status=Location.PublicationStatus.PUBLISHED,
            verification_state=VerificationState.FIELD_VERIFIED,
            representative_latitude=Decimal("6.5190"),
            representative_longitude=Decimal("3.3750"),
        )

        self.entrance_a = Entrance.objects.create(
            location=self.loc_a,
            name="Alpha Entrance",
            latitude=Decimal("6.5180"),
            longitude=Decimal("3.3740"),
            verification_state=VerificationState.FIELD_VERIFIED,
            is_active=True,
            is_primary=True,
        )
        self.entrance_b = Entrance.objects.create(
            location=self.loc_b,
            name="Beta Entrance",
            latitude=Decimal("6.5190"),
            longitude=Decimal("3.3750"),
            verification_state=VerificationState.FIELD_VERIFIED,
            is_active=True,
            is_primary=True,
        )

        # Create two nodes
        self.node_a = WalkableNode.objects.create(
            latitude=Decimal("6.5180"),
            longitude=Decimal("3.3740"),
            label="1",
            verification_state=VerificationState.FIELD_VERIFIED,
        )
        self.node_b = WalkableNode.objects.create(
            latitude=Decimal("6.5190"),
            longitude=Decimal("3.3750"),
            label="2",
            verification_state=VerificationState.FIELD_VERIFIED,
        )

        # Connect entrances to nodes
        EntranceNetworkAnchor.objects.create(
            entrance=self.entrance_a,
            node=self.node_a,
            is_active=True,
            verification_state=VerificationState.FIELD_VERIFIED,
        )
        EntranceNetworkAnchor.objects.create(
            entrance=self.entrance_b,
            node=self.node_b,
            is_active=True,
            verification_state=VerificationState.FIELD_VERIFIED,
        )

        # Connect nodes with segment
        geom = {
            "type": "LineString",
            "coordinates": [[3.3740, 6.5180], [3.3750, 6.5190]],
        }
        self.segment = WalkableSegment.objects.create(
            start_node=self.node_a,
            end_node=self.node_b,
            geometry=geom,
            label="A",
            verification_state=VerificationState.FIELD_VERIFIED,
        )

    def test_public_route_returns_field_verified_when_all_elements_verified(self):
        url = reverse("routing:public-route")
        response = self.client.get(url, {
            "origin": f"location:{self.loc_a.id}",
            "destination": f"location:{self.loc_b.id}",
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["summary"]["verification_state"], VerificationState.FIELD_VERIFIED)
        self.assertEqual(data["route"]["properties"]["route_state"], VerificationState.FIELD_VERIFIED)

    def test_public_route_returns_unverified_when_any_element_unverified(self):
        self.segment.verification_state = VerificationState.UNVERIFIED
        self.segment.save()

        url = reverse("routing:public-route")
        response = self.client.get(url, {
            "origin": f"location:{self.loc_a.id}",
            "destination": f"location:{self.loc_b.id}",
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["summary"]["verification_state"], VerificationState.UNVERIFIED)
        self.assertEqual(data["route"]["properties"]["route_state"], VerificationState.UNVERIFIED)

    def test_live_route_returns_field_verified_when_all_network_elements_verified(self):
        url = reverse("routing:public-route-from-position")
        payload = {
            "position": {
                "longitude": 3.3740,
                "latitude": 6.5180,
                "accuracy_metres": 5.0,
            },
            "destination": f"location:{self.loc_b.id}",
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["summary"]["verification_state"], VerificationState.FIELD_VERIFIED)
        self.assertEqual(data["route"]["properties"]["route_state"], VerificationState.FIELD_VERIFIED)
