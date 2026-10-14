from datetime import timedelta
from decimal import Decimal
from io import StringIO
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from locations.models import Entrance, Floor, InternalPlace, Location
from routing.models import (
    EntranceNetworkAnchor,
    LocationNetworkAnchor,
    SegmentVerificationRecord,
    VerificationState,
    WalkableNode,
    WalkableSegment,
)
from routing.management.commands.verify_current_map_baseline import BASELINE_SNAPSHOT_CUTOFF


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
        self.floor = Floor.objects.create(
            location=self.published_loc,
            level=0,
            label="Ground floor",
        )
        self.published_internal = InternalPlace.objects.create(
            location=self.published_loc,
            floor=self.floor,
            name="Student help desk",
            internal_type=InternalPlace.Type.OFFICE,
            publication_status=Location.PublicationStatus.PUBLISHED,
            verification_state=Location.VerificationState.UNVERIFIED,
        )
        self.draft_internal = InternalPlace.objects.create(
            location=self.published_loc,
            floor=self.floor,
            name="Draft room",
            internal_type=InternalPlace.Type.OTHER,
            publication_status=Location.PublicationStatus.DRAFT,
            verification_state=Location.VerificationState.UNVERIFIED,
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
        # The command deliberately falls back to source reference/UUID when
        # creation timestamps tie. Make this test's intended creation order
        # independent of filesystem/SQLite clock resolution.
        node_created_at = timezone.now()
        WalkableNode.objects.filter(pk=self.node1.pk).update(created_at=node_created_at)
        WalkableNode.objects.filter(pk=self.node2.pk).update(
            created_at=node_created_at + timedelta(microseconds=1),
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
        self.location_anchor = LocationNetworkAnchor.objects.create(
            location=self.published_loc,
            node=self.node1,
            is_active=True,
            verification_state=VerificationState.UNVERIFIED,
        )
        self.draft_location_anchor = LocationNetworkAnchor.objects.create(
            location=self.draft_loc,
            node=self.node2,
            is_active=True,
            verification_state=VerificationState.UNVERIFIED,
        )

        # The command is deliberately locked to the owner-approved historical
        # snapshot. Tests opt these fixtures into that snapshot explicitly so
        # their behavior does not depend on the machine's current clock.
        snapshot_time = BASELINE_SNAPSHOT_CUTOFF - timedelta(seconds=1)
        for item in (
            self.published_loc, self.draft_loc, self.active_entrance,
            self.draft_loc_entrance, self.inactive_entrance,
            self.published_internal, self.draft_internal,
            self.node1, self.node2, self.segment1, self.anchor,
            self.location_anchor, self.draft_location_anchor,
        ):
            type(item).objects.filter(pk=item.pk).update(updated_at=snapshot_time)

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
        self.assertIn("InternalPlaces: 1 eligible", output)
        self.assertIn("Entrances: 1 eligible", output)
        self.assertIn("WalkableNodes: 2 eligible", output)
        self.assertIn("WalkableSegments: 1 eligible", output)
        self.assertIn("LocationNetworkAnchors: 1 eligible", output)
        self.assertIn("EntranceNetworkAnchors: 1 eligible", output)
        self.assertIn("Main Building / Student help desk", output)
        self.assertNotIn("Main Building / Draft room", output)

        # Database state untouched
        self.published_loc.refresh_from_db()
        self.assertEqual(self.published_loc.verification_state, VerificationState.UNVERIFIED)
        self.published_internal.refresh_from_db()
        self.assertEqual(self.published_internal.verification_state, VerificationState.UNVERIFIED)

    def test_verify_current_map_baseline_apply_and_idempotency(self):
        out = StringIO()
        call_command("verify_current_map_baseline", "--apply", stdout=out)
        output = out.getvalue()
        self.assertIn("Mode: APPLY", output)
        self.assertIn(
            "Successfully marked 1 Locations, 1 Entrances, 1 InternalPlaces, 2 Nodes, 1 Segments, "
            "1 LocationNetworkAnchors, and 1 EntranceNetworkAnchors as FIELD_VERIFIED",
            output,
        )

        self.published_loc.refresh_from_db()
        self.draft_loc.refresh_from_db()
        self.active_entrance.refresh_from_db()
        self.draft_loc_entrance.refresh_from_db()
        self.inactive_entrance.refresh_from_db()
        self.published_internal.refresh_from_db()
        self.draft_internal.refresh_from_db()
        self.node1.refresh_from_db()
        self.segment1.refresh_from_db()
        self.anchor.refresh_from_db()
        self.location_anchor.refresh_from_db()
        self.draft_location_anchor.refresh_from_db()

        # Published and active items are now FIELD_VERIFIED
        self.assertEqual(self.published_loc.verification_state, VerificationState.FIELD_VERIFIED)
        self.assertEqual(self.active_entrance.verification_state, VerificationState.FIELD_VERIFIED)
        self.assertEqual(self.published_internal.verification_state, VerificationState.FIELD_VERIFIED)
        self.assertEqual(self.node1.verification_state, VerificationState.FIELD_VERIFIED)
        self.assertEqual(self.segment1.verification_state, VerificationState.FIELD_VERIFIED)
        self.assertEqual(self.anchor.verification_state, VerificationState.FIELD_VERIFIED)
        self.assertEqual(self.location_anchor.verification_state, VerificationState.FIELD_VERIFIED)

        # Draft/inactive items remain UNVERIFIED
        self.assertEqual(self.draft_loc.verification_state, VerificationState.UNVERIFIED)
        self.assertEqual(self.draft_loc_entrance.verification_state, VerificationState.UNVERIFIED)
        self.assertEqual(self.inactive_entrance.verification_state, VerificationState.UNVERIFIED)
        self.assertEqual(self.draft_internal.verification_state, VerificationState.UNVERIFIED)
        self.assertEqual(self.draft_location_anchor.verification_state, VerificationState.UNVERIFIED)

        # Verification audit record created
        audit = SegmentVerificationRecord.objects.get(segment=self.segment1)
        self.assertEqual(audit.action, SegmentVerificationRecord.Action.GRANTED)
        self.assertEqual(audit.reason, "Owner-approved final map baseline")

        # Idempotent re-run
        out2 = StringIO()
        call_command("verify_current_map_baseline", "--apply", stdout=out2)
        # Should not create duplicate audit records
        self.assertEqual(SegmentVerificationRecord.objects.filter(segment=self.segment1).count(), 1)

    def test_verify_current_map_baseline_never_promotes_demo_records(self):
        demo_location = Location.objects.create(
            name="DEMO — Test place",
            category="building",
            publication_status=Location.PublicationStatus.PUBLISHED,
            verification_state=Location.VerificationState.DEMO,
            representative_latitude=Decimal("6.5170"),
            representative_longitude=Decimal("3.3730"),
        )
        demo_floor = Floor.objects.create(location=demo_location, level=0, label="Demo floor")
        demo_internal = InternalPlace.objects.create(
            location=demo_location,
            floor=demo_floor,
            name="DEMO — Room",
            internal_type=InternalPlace.Type.OTHER,
            publication_status=Location.PublicationStatus.PUBLISHED,
            verification_state=Location.VerificationState.DEMO,
        )
        demo_entrance = Entrance.objects.create(
            location=demo_location,
            name="DEMO — Entrance",
            latitude=Decimal("6.5170"),
            longitude=Decimal("3.3730"),
            verification_state=Location.VerificationState.DEMO,
            is_active=True,
        )
        demo_node_a = WalkableNode.objects.create(
            latitude=Decimal("6.5170"), longitude=Decimal("3.3730"),
            verification_state=VerificationState.DEMO,
        )
        demo_node_b = WalkableNode.objects.create(
            latitude=Decimal("6.5171"), longitude=Decimal("3.3731"),
            verification_state=VerificationState.DEMO,
        )
        demo_segment = WalkableSegment.objects.create(
            start_node=demo_node_a,
            end_node=demo_node_b,
            geometry={
                "type": "LineString",
                "coordinates": [[3.3730, 6.5170], [3.3731, 6.5171]],
            },
            verification_state=VerificationState.DEMO,
        )
        demo_location_anchor = LocationNetworkAnchor.objects.create(
            location=demo_location,
            node=demo_node_a,
            verification_state=VerificationState.DEMO,
            is_active=True,
        )
        demo_entrance_anchor = EntranceNetworkAnchor.objects.create(
            entrance=demo_entrance,
            node=demo_node_a,
            verification_state=VerificationState.DEMO,
            is_active=True,
        )

        snapshot_time = BASELINE_SNAPSHOT_CUTOFF - timedelta(seconds=1)
        for item in (
            demo_location, demo_internal, demo_entrance, demo_node_a,
            demo_node_b, demo_segment, demo_location_anchor,
            demo_entrance_anchor,
        ):
            type(item).objects.filter(pk=item.pk).update(updated_at=snapshot_time)

        call_command("verify_current_map_baseline", "--apply", stdout=StringIO())

        for item in (
            demo_location, demo_internal, demo_entrance, demo_node_a, demo_node_b,
            demo_segment, demo_location_anchor, demo_entrance_anchor,
        ):
            item.refresh_from_db()
            self.assertEqual(item.verification_state, VerificationState.DEMO)

    def test_verify_current_map_baseline_never_promotes_records_after_snapshot(self):
        future_location = Location.objects.create(
            name="Future published place",
            category="building",
            publication_status=Location.PublicationStatus.PUBLISHED,
            verification_state=VerificationState.UNVERIFIED,
            representative_latitude=Decimal("6.5172"),
            representative_longitude=Decimal("3.3732"),
        )
        future_floor = Floor.objects.create(
            location=future_location,
            level=0,
            label="Ground floor",
        )
        future_internal = InternalPlace.objects.create(
            location=future_location,
            floor=future_floor,
            name="Future room",
            internal_type=InternalPlace.Type.OTHER,
            publication_status=Location.PublicationStatus.PUBLISHED,
            verification_state=VerificationState.UNVERIFIED,
        )
        future_entrance = Entrance.objects.create(
            location=future_location,
            name="Future entrance",
            latitude=Decimal("6.5172"),
            longitude=Decimal("3.3732"),
            verification_state=VerificationState.UNVERIFIED,
            is_active=True,
        )
        future_node_a = WalkableNode.objects.create(
            latitude=Decimal("6.5172"), longitude=Decimal("3.3732"),
            verification_state=VerificationState.UNVERIFIED,
        )
        future_node_b = WalkableNode.objects.create(
            latitude=Decimal("6.5173"), longitude=Decimal("3.3733"),
            verification_state=VerificationState.UNVERIFIED,
        )
        future_segment = WalkableSegment.objects.create(
            start_node=future_node_a,
            end_node=future_node_b,
            geometry={
                "type": "LineString",
                "coordinates": [[3.3732, 6.5172], [3.3733, 6.5173]],
            },
            verification_state=VerificationState.UNVERIFIED,
        )
        future_location_anchor = LocationNetworkAnchor.objects.create(
            location=future_location,
            node=future_node_a,
            verification_state=VerificationState.UNVERIFIED,
            is_active=True,
        )
        future_entrance_anchor = EntranceNetworkAnchor.objects.create(
            entrance=future_entrance,
            node=future_node_a,
            verification_state=VerificationState.UNVERIFIED,
            is_active=True,
        )
        after_snapshot = BASELINE_SNAPSHOT_CUTOFF + timedelta(seconds=1)
        future_items = (
            future_location, future_internal, future_entrance,
            future_node_a, future_node_b, future_segment,
            future_location_anchor, future_entrance_anchor,
        )
        for item in future_items:
            type(item).objects.filter(pk=item.pk).update(updated_at=after_snapshot)

        call_command("verify_current_map_baseline", "--apply", stdout=StringIO())

        for item in future_items:
            item.refresh_from_db()
            self.assertEqual(item.verification_state, VerificationState.UNVERIFIED)
