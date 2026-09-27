from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from contributions.models import Contribution
from locations.models import Entrance, InternalPlace, Location
from routing.models import EntranceNetworkAnchor, WalkableNode, WalkableSegment


class PredeploymentCleanupCommandTests(TestCase):
    fixtures = ["demo_locations.json"]

    def setUp(self):
        self.new_building = Location.objects.create(
            name="New Building",
            publication_status=Location.PublicationStatus.PUBLISHED,
            verification_state=Location.VerificationState.UNVERIFIED,
            representative_latitude="6.518475",
            representative_longitude="3.372694",
            is_active=True,
        )
        self.sports = Location.objects.create(
            name="Sports Complex",
            publication_status=Location.PublicationStatus.PUBLISHED,
            verification_state=Location.VerificationState.UNVERIFIED,
            representative_latitude="6.518525",
            representative_longitude="3.374192",
            is_active=True,
        )
        self.sports_gate = Entrance.objects.create(
            location=self.sports,
            name="Gate 1",
            latitude="6.518877",
            longitude="3.373512",
            is_primary=True,
            verification_state=Location.VerificationState.DEMO,
        )
        self.node_a = WalkableNode.objects.create(
            longitude="3.373500",
            latitude="6.518800",
            verification_state="UNVERIFIED",
            source_type="OSM",
        )
        self.node_b = WalkableNode.objects.create(
            longitude="3.374000",
            latitude="6.518800",
            verification_state="UNVERIFIED",
            source_type="OSM",
        )
        self.segment = WalkableSegment.objects.create(
            start_node=self.node_a,
            end_node=self.node_b,
            geometry={
                "type": "LineString",
                "coordinates": [[3.3735, 6.5188], [3.374, 6.5188]],
            },
            verification_state="UNVERIFIED",
            source_type="OSM",
        )
        EntranceNetworkAnchor.objects.create(
            entrance=self.sports_gate,
            node=self.node_a,
            verification_state="UNVERIFIED",
        )
        library = Location.objects.get(pk="10000000-0000-4000-8000-000000000002")
        Contribution.objects.create(
            request_id="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            status=Contribution.Status.APPROVED,
            contribution_type=Contribution.Type.CORRECT_LOCATION,
            target_location=library,
            description="Disposable owner-test correction.",
        )

    def test_default_is_a_rolled_back_dry_run(self):
        output = StringIO()
        call_command("cleanup_predeployment_data", stdout=output)

        self.assertEqual(Location.objects.filter(verification_state="DEMO").count(), 6)
        self.sports_gate.refresh_from_db()
        self.assertEqual(self.sports_gate.verification_state, "DEMO")
        self.assertEqual(Contribution.objects.count(), 1)
        self.assertIn("all changes rolled back", output.getvalue())

    def test_apply_removes_known_test_data_but_preserves_operational_graph(self):
        call_command("cleanup_predeployment_data", apply=True, stdout=StringIO())

        self.assertEqual(
            set(Location.objects.values_list("name", flat=True)),
            {"New Building", "Sports Complex"},
        )
        self.assertFalse(Contribution.objects.exists())
        self.assertEqual(WalkableNode.objects.count(), 2)
        self.assertEqual(WalkableSegment.objects.count(), 1)
        self.assertTrue(EntranceNetworkAnchor.objects.filter(entrance=self.sports_gate).exists())
        self.sports_gate.refresh_from_db()
        self.assertEqual(self.sports_gate.verification_state, "UNVERIFIED")

    def test_apply_is_safe_to_repeat(self):
        call_command("cleanup_predeployment_data", apply=True, stdout=StringIO())
        call_command("cleanup_predeployment_data", apply=True, stdout=StringIO())

        self.assertEqual(Location.objects.count(), 2)
        self.assertEqual(InternalPlace.objects.count(), 0)
