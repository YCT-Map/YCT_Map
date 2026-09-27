from decimal import Decimal
import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from locations.models import Entrance, Location
from routing.destinations import resolve_destination
from routing.editor_services import entrance_node_candidates
from routing.models import EntranceNetworkAnchor, SourceType, VerificationState, WalkableNode, WalkableSegment


class EntranceRoutingConnectionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.editor = get_user_model().objects.create_user("anchor-editor", password="Strong-test-password-42")
        cls.editor.groups.add(Group.objects.get(name="Editor"))
        cls.place = Location.objects.create(
            name="TEST — Sports Complex",
            place_type=Location.PlaceType.RECREATION_AREA,
            publication_status=Location.PublicationStatus.PUBLISHED,
            verification_state=Location.VerificationState.UNVERIFIED,
            representative_latitude=Decimal("6.518000"),
            representative_longitude=Decimal("3.374000"),
            is_active=True,
        )
        cls.entrance = Entrance.objects.create(
            location=cls.place,
            name="Gate 1",
            latitude=Decimal("6.518000"),
            longitude=Decimal("3.374000"),
            is_primary=True,
            is_active=True,
            verification_state=Location.VerificationState.UNVERIFIED,
        )
        cls.near_node = cls._node("6.518100", "3.374000", "Near junction")
        cls.second_node = cls._node("6.518220", "3.374000", "Second junction")
        cls.questionable_node = cls._node("6.518550", "3.374000", "Questionable junction")
        cls.far_node = cls._node("6.519000", "3.374000", "Far junction")
        cls.inactive_node = cls._node("6.518050", "3.374000", "Inactive junction", active=False)
        cls._segment(cls.near_node, cls.second_node)
        cls._segment(cls.second_node, cls.questionable_node)
        cls._segment(cls.questionable_node, cls.far_node)

    @classmethod
    def _node(cls, latitude, longitude, label, active=True):
        return WalkableNode.objects.create(
            label=label,
            latitude=Decimal(latitude),
            longitude=Decimal(longitude),
            source_type=SourceType.MANUAL,
            verification_state=VerificationState.UNVERIFIED,
            is_active=active,
        )

    @classmethod
    def _segment(cls, start, end):
        return WalkableSegment.objects.create(
            start_node=start,
            end_node=end,
            geometry={
                "type": "LineString",
                "coordinates": [
                    [float(start.longitude), float(start.latitude)],
                    [float(end.longitude), float(end.latitude)],
                ],
            },
            is_bidirectional=True,
            source_type=SourceType.MANUAL,
            verification_state=VerificationState.UNVERIFIED,
            is_active=True,
        )

    def setUp(self):
        self.client.force_login(self.editor)
        self.candidates_url = reverse(
            "editor:entrance-connection-candidates", args=(self.place.pk, self.entrance.pk)
        )
        self.update_url = reverse(
            "editor:entrance-connection-update", args=(self.place.pk, self.entrance.pk)
        )

    def connector(self, node, *bends):
        return json.dumps({
            "type": "LineString",
            "coordinates": [
                [float(node.longitude), float(node.latitude)],
                *[list(point) for point in bends],
                [float(self.entrance.longitude), float(self.entrance.latitude)],
            ],
        })

    def test_disconnected_entrance_exposes_map_first_connection_workflow(self):
        response = self.client.get(reverse("editor:entrance-edit", args=(self.place.pk, self.entrance.pk)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Not connected to walking network.")
        self.assertContains(response, "Find nearby connection")
        self.assertContains(response, self.candidates_url)
        self.assertContains(response, 'id="routing-node-id"')
        self.assertContains(response, "editor-entrance-map.js")

    def test_candidates_are_connected_active_nodes_ordered_by_distance(self):
        candidates = entrance_node_candidates(self.entrance)
        self.assertEqual([item["node"] for item in candidates], [
            self.near_node, self.second_node, self.questionable_node,
        ])
        self.assertEqual([item["distance_band"] for item in candidates], ["nearby", "nearby", "questionable"])
        self.assertNotIn(self.inactive_node, [item["node"] for item in candidates])
        self.assertNotIn(self.far_node, [item["node"] for item in candidates])

    def test_opening_candidates_is_read_only_and_returns_map_data(self):
        response = self.client.get(self.candidates_url)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual([item["id"] for item in body["candidates"]], [
            str(self.near_node.pk), str(self.second_node.pk), str(self.questionable_node.pk),
        ])
        self.assertTrue(any(feature["properties"]["kind"] == "segment" for feature in body["map"]["features"]))
        self.assertFalse(EntranceNetworkAnchor.objects.filter(entrance=self.entrance).exists())

    def test_confirmation_creates_unverified_anchor_without_changing_place_or_points(self):
        original = {
            "publication": self.place.publication_status,
            "verification": self.place.verification_state,
            "representative": (self.place.representative_latitude, self.place.representative_longitude),
            "entrance": (self.entrance.latitude, self.entrance.longitude, self.entrance.verification_state),
        }
        response = self.client.post(self.update_url, {
            "action": "connect", "node_id": self.near_node.pk,
            "connector_geometry": self.connector(self.near_node),
        })
        self.assertRedirects(response, reverse("editor:entrance-edit", args=(self.place.pk, self.entrance.pk)))
        anchor = EntranceNetworkAnchor.objects.get(entrance=self.entrance)
        self.assertEqual(anchor.node, self.near_node)
        self.assertTrue(anchor.is_active)
        self.assertEqual(anchor.verification_state, VerificationState.UNVERIFIED)
        self.assertEqual(anchor.connector_geometry["coordinates"][-1], [3.374, 6.518])
        self.place.refresh_from_db()
        self.entrance.refresh_from_db()
        self.assertEqual(self.place.publication_status, original["publication"])
        self.assertEqual(self.place.verification_state, original["verification"])
        self.assertEqual((self.place.representative_latitude, self.place.representative_longitude), original["representative"])
        self.assertEqual((self.entrance.latitude, self.entrance.longitude, self.entrance.verification_state), original["entrance"])

    def test_changing_connection_updates_single_anchor_only_after_confirmation(self):
        anchor = EntranceNetworkAnchor.objects.create(
            entrance=self.entrance, node=self.near_node,
            verification_state=VerificationState.UNVERIFIED, is_active=True,
        )
        self.client.get(self.candidates_url)
        anchor.refresh_from_db()
        self.assertEqual(anchor.node, self.near_node)
        self.client.post(self.update_url, {
            "action": "connect", "node_id": self.second_node.pk,
            "connector_geometry": self.connector(self.second_node),
        })
        anchor.refresh_from_db()
        self.assertEqual(anchor.node, self.second_node)
        self.assertEqual(EntranceNetworkAnchor.objects.filter(entrance=self.entrance).count(), 1)

    def test_distant_or_inactive_node_cannot_be_forced_by_post(self):
        for node in (self.far_node, self.inactive_node):
            with self.subTest(node=node):
                response = self.client.post(self.update_url, {
                    "action": "connect", "node_id": node.pk,
                    "connector_geometry": self.connector(node),
                }, follow=True)
                self.assertContains(response, "Choose one of the suitable active routing nodes")
                self.assertFalse(EntranceNetworkAnchor.objects.filter(entrance=self.entrance).exists())

    def test_published_place_becomes_routable_only_after_anchor_confirmation(self):
        before = resolve_destination(f"location:{self.place.pk}", allow_legacy=False)
        self.assertFalse(before.routing_available)
        self.assertEqual(self.place.publication_status, Location.PublicationStatus.PUBLISHED)
        self.client.post(self.update_url, {
            "action": "connect", "node_id": self.near_node.pk,
            "connector_geometry": self.connector(self.near_node),
        })
        after = resolve_destination(f"location:{self.place.pk}", allow_legacy=False)
        self.assertTrue(after.routing_available)
        self.assertEqual(after.node, self.near_node)

    def test_disconnect_requires_explicit_confirmation_and_preserves_graph(self):
        anchor = EntranceNetworkAnchor.objects.create(
            entrance=self.entrance, node=self.near_node,
            verification_state=VerificationState.UNVERIFIED, is_active=True,
        )
        segment_count = WalkableSegment.objects.count()
        self.client.post(self.update_url, {"action": "disconnect"})
        anchor.refresh_from_db()
        self.assertTrue(anchor.is_active)
        self.client.post(self.update_url, {"action": "disconnect", "confirm_disconnect": "yes"})
        anchor.refresh_from_db()
        self.assertFalse(anchor.is_active)
        self.assertEqual(WalkableSegment.objects.count(), segment_count)

    def test_public_and_underprivileged_users_cannot_access_connection_workflow(self):
        self.client.logout()
        response = self.client.get(self.candidates_url)
        self.assertEqual(response.status_code, 302)
        viewer = get_user_model().objects.create_user("anchor-viewer", password="Strong-test-password-42")
        self.client.force_login(viewer)
        self.assertEqual(self.client.get(self.candidates_url).status_code, 403)
        self.assertEqual(
            self.client.post(self.update_url, {"action": "connect", "node_id": self.near_node.pk}).status_code,
            403,
        )

    def test_unrelated_existing_anchor_is_unchanged(self):
        other = Location.objects.create(name="DEMO — Existing", place_type=Location.PlaceType.BUILDING)
        other_entrance = Entrance.objects.create(
            location=other, name="Primary", latitude=Decimal("6.518100"), longitude=Decimal("3.374000"),
            is_primary=True, is_active=True,
        )
        existing = EntranceNetworkAnchor.objects.create(
            entrance=other_entrance, node=self.near_node,
            verification_state=VerificationState.DEMO, is_active=True,
        )
        self.client.get(self.candidates_url)
        self.client.post(self.update_url, {
            "action": "connect", "node_id": self.second_node.pk,
            "connector_geometry": self.connector(self.second_node),
        })
        existing.refresh_from_db()
        self.assertEqual(existing.node, self.near_node)
        self.assertEqual(existing.verification_state, VerificationState.DEMO)
        self.assertTrue(existing.is_active)

    def test_malformed_and_reversed_connector_geometry_is_rejected(self):
        malformed = self.client.post(self.update_url, {
            "action": "connect", "node_id": self.near_node.pk, "connector_geometry": "not-json",
        }, follow=True)
        self.assertContains(malformed, "valid approved arrival connector")
        reversed_geometry = json.dumps({
            "type": "LineString",
            "coordinates": [[6.518100, 3.374000], [6.518000, 3.374000]],
        })
        reversed_response = self.client.post(self.update_url, {
            "action": "connect", "node_id": self.near_node.pk,
            "connector_geometry": reversed_geometry,
        }, follow=True)
        self.assertContains(reversed_response, "connector must begin exactly")
        self.assertFalse(EntranceNetworkAnchor.objects.filter(entrance=self.entrance).exists())
