from decimal import Decimal
from io import StringIO
from django.core.management import call_command
from django.test import TestCase

from locations.models import Entrance, Location
from routing.models import (
    EntranceNetworkAnchor,
    SegmentVerificationRecord,
    VerificationState,
    WalkableNode,
    WalkableSegment,
)


class ManagementCommandsTests(TestCase):
    def setUp(self):
        # Create published location and unpublished location
        self.published_loc = Location.objects.create(
            name="Main Building",
            category="building",
            publication_status=Location.PublicationStatus.PUBLISHED,
            verification_state=VerificationState.UNVERIFIED,
            representative_latitude=Decimal("6.5185"),
            representative_longitude=Decimal("3.3742"),
        )
        self.draft_loc = Location.objects.create(
            name="Draft Building",
            category="building",
            publication_status=Location.PublicationStatus.DRAFT,
            verification_state=VerificationState.UNVERIFIED,
            representative_latitude=Decimal("6.5190"),
            representative_longitude=Decimal("3.3750"),
        )

        # Entrances
        self.active_entrance = Entrance.objects.create(
            location=self.published_loc,
            name="Front Gate",
            latitude=Decimal("6.5185"),
            longitude=Decimal("3.3742"),
            verification_state=VerificationState.UNVERIFIED,
            is_active=True,
        )
        self.draft_loc_entrance = Entrance.objects.create(
            location=self.draft_loc,
            name="Draft Gate",
            latitude=Decimal("6.5190"),
            longitude=Decimal("3.3750"),
            verification_state=VerificationState.UNVERIFIED,
            is_active=True,
        )
        self.inactive_entrance = Entrance.objects.create(
            location=self.published_loc,
            name="Old Gate",
            latitude=Decimal("6.5184"),
            longitude=Decimal("3.3741"),
            verification_state=VerificationState.UNVERIFIED,
            is_active=False,
        )

        # Nodes
        self.node1 = WalkableNode.objects.create(
            latitude=Decimal("6.5185"),
            longitude=Decimal("3.3742"),
            label="node_legacy_99",
            source_reference="osm_node_1001",
            source_type="osm",
            verification_state=VerificationState.UNVERIFIED,
        )
        self.node2 = WalkableNode.objects.create(
            latitude=Decimal("6.5186"),
            longitude=Decimal("3.3743"),
            label="custom_node",
            source_reference="QA Node A",
            source_type="manual",
            verification_state=VerificationState.UNVERIFIED,
        )

        # Segment
        geom = {
            "type": "LineString",
            "coordinates": [[3.3742, 6.5185], [3.3743, 6.5186]],
        }
        self.segment1 = WalkableSegment.objects.create(
            start_node=self.node1,
            end_node=self.node2,
            geometry=geom,
            label="way_legacy_88",
            source_reference="osm_way_2001",
            source_type="osm",
            verification_state=VerificationState.UNVERIFIED,
        )

        # Anchor
        self.anchor = EntranceNetworkAnchor.objects.create(
            entrance=self.active_entrance,
            node=self.node1,
            is_active=True,
            verification_state=VerificationState.UNVERIFIED,
        )

    def test_assign_graph_display_labels_dry_run(self):
        out = StringIO()
        call_command("assign_graph_display_labels", "--dry-run", stdout=out)
        output = out.getvalue()
        self.assertIn("Mode: DRY-RUN (read-only)", output)
        self.assertIn("Nodes: 2 total, 2 to update", output)
        self.assertIn("Segments: 1 total, 1 to update", output)

        # Database should NOT have changed
        self.node1.refresh_from_db()
        self.assertEqual(self.node1.label, "node_legacy_99")

    def test_assign_graph_display_labels_apply_and_idempotency(self):
        out = StringIO()
        call_command("assign_graph_display_labels", "--apply", stdout=out)
        output = out.getvalue()
        self.assertIn("Mode: APPLY", output)
        self.assertIn("Successfully updated 2 nodes and 1 segments", output)

        self.node1.refresh_from_db()
        self.node2.refresh_from_db()
        self.segment1.refresh_from_db()

        # Labels are numeric for nodes and alphabetic for segments
        self.assertEqual(self.node1.label, "1")
        self.assertEqual(self.node2.label, "2")
        self.assertEqual(self.segment1.label, "A")
        # Provenance source_reference is preserved
        self.assertEqual(self.node1.source_reference, "osm_node_1001")
        self.assertEqual(self.node2.source_reference, "QA Node A")
        self.assertEqual(self.segment1.source_reference, "osm_way_2001")

        # Test display_label helper property
        self.assertEqual(self.node1.display_label, "Node 1")
        self.assertEqual(self.segment1.display_label, "Segment A")

        # Re-running with apply is idempotent:
        out2 = StringIO()
        call_command("assign_graph_display_labels", "--apply", stdout=out2)
        self.node1.refresh_from_db()
        self.node2.refresh_from_db()
        self.segment1.refresh_from_db()
        self.assertEqual(self.node1.label, "1")
        self.assertEqual(self.node2.label, "2")
        self.assertEqual(self.segment1.label, "A")

    def test_verify_current_map_baseline_dry_run(self):
        out = StringIO()
        call_command("verify_current_map_baseline", "--dry-run", stdout=out)
        output = out.getvalue()
        self.assertIn("Mode: DRY-RUN (read-only)", output)
        self.assertIn("Locations: 1 eligible", output)
        self.assertIn("Entrances: 1 eligible", output)
        self.assertIn("WalkableNodes: 2 eligible", output)
        self.assertIn("WalkableSegments: 1 eligible", output)

        # Database state untouched
        self.published_loc.refresh_from_db()
        self.assertEqual(self.published_loc.verification_state, VerificationState.UNVERIFIED)

    def test_verify_current_map_baseline_apply_and_idempotency(self):
        out = StringIO()
        call_command("verify_current_map_baseline", "--apply", stdout=out)
        output = out.getvalue()
        self.assertIn("Mode: APPLY", output)
        self.assertIn("Successfully marked 1 Locations, 1 Entrances, 2 Nodes, and 1 Segments as FIELD_VERIFIED", output)

        self.published_loc.refresh_from_db()
        self.draft_loc.refresh_from_db()
        self.active_entrance.refresh_from_db()
        self.draft_loc_entrance.refresh_from_db()
        self.inactive_entrance.refresh_from_db()
        self.node1.refresh_from_db()
        self.segment1.refresh_from_db()
        self.anchor.refresh_from_db()

        # Published and active items are now FIELD_VERIFIED
        self.assertEqual(self.published_loc.verification_state, VerificationState.FIELD_VERIFIED)
        self.assertEqual(self.active_entrance.verification_state, VerificationState.FIELD_VERIFIED)
        self.assertEqual(self.node1.verification_state, VerificationState.FIELD_VERIFIED)
        self.assertEqual(self.segment1.verification_state, VerificationState.FIELD_VERIFIED)
        self.assertEqual(self.anchor.verification_state, VerificationState.FIELD_VERIFIED)

        # Draft/inactive items remain UNVERIFIED
        self.assertEqual(self.draft_loc.verification_state, VerificationState.UNVERIFIED)
        self.assertEqual(self.draft_loc_entrance.verification_state, VerificationState.UNVERIFIED)
        self.assertEqual(self.inactive_entrance.verification_state, VerificationState.UNVERIFIED)

        # Verification audit record created
        audit = SegmentVerificationRecord.objects.get(segment=self.segment1)
        self.assertEqual(audit.action, SegmentVerificationRecord.Action.GRANTED)
        self.assertEqual(audit.reason, "Owner-approved final map baseline")

        # Idempotent re-run
        out2 = StringIO()
        call_command("verify_current_map_baseline", "--apply", stdout=out2)
        # Should not create duplicate audit records
        self.assertEqual(SegmentVerificationRecord.objects.filter(segment=self.segment1).count(), 1)
