"""Explicitly verify the owner-accepted 2026-10-14 campus snapshot.

The command intentionally promotes only ``UNVERIFIED`` records. Demonstration
records, drafts, inactive graph history, and records changed after the locked
snapshot remain untouched.
"""

from datetime import datetime, timezone as datetime_timezone

from django.core.management.base import BaseCommand
from django.db import transaction

from locations.models import Entrance, InternalPlace, Location
from routing.models import (EntranceNetworkAnchor, LocationNetworkAnchor,
                            SegmentVerificationRecord, VerificationState,
                            WalkableNode, WalkableSegment)

AUDIT_REASON = "Owner-approved final map baseline"
BASELINE_SNAPSHOT_CUTOFF = datetime(2026, 10, 14, tzinfo=datetime_timezone.utc)


class Command(BaseCommand):
    help = (
        "Mark the accepted current public/active map baseline as FIELD_VERIFIED "
        "without changing DEMO, draft, archived, or inactive records."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulate the baseline verification without modifying database records.",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Apply the baseline verification and persist FIELD_VERIFIED states.",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run")
        apply_changes = options.get("apply")

        if not apply_changes:
            dry_run = True

        self.stdout.write(self.style.MIGRATE_HEADING("=== YCT Map Accepted Baseline Verification ==="))
        mode_str = "APPLY" if apply_changes else "DRY-RUN (read-only)"
        self.stdout.write(f"Mode: {mode_str}\n")
        self.stdout.write(f"Audit reason: \"{AUDIT_REASON}\"\n")
        self.stdout.write(
            f"Snapshot cutoff: {BASELINE_SNAPSHOT_CUTOFF.isoformat()} "
            "(records updated at/after this time are excluded)\n"
        )

        # 1. LOCATIONS (Published outdoor places)
        all_locations = Location.objects.all()
        eligible_locations = all_locations.filter(
            publication_status=Location.PublicationStatus.PUBLISHED,
            updated_at__lt=BASELINE_SNAPSHOT_CUTOFF,
        )
        locations_to_verify = eligible_locations.filter(
            verification_state=Location.VerificationState.UNVERIFIED,
        )
        locations_already_verified = eligible_locations.filter(
            verification_state=Location.VerificationState.FIELD_VERIFIED,
        ).count()
        locations_skipped = all_locations.exclude(pk__in=eligible_locations.values("pk")).count()

        # 2. INTERNAL PLACES (Published records under published places)
        all_internal_places = InternalPlace.objects.all()
        eligible_internal_places = all_internal_places.filter(
            publication_status=Location.PublicationStatus.PUBLISHED,
            location__publication_status=Location.PublicationStatus.PUBLISHED,
            updated_at__lt=BASELINE_SNAPSHOT_CUTOFF,
            location__updated_at__lt=BASELINE_SNAPSHOT_CUTOFF,
        )
        internal_places_to_verify = eligible_internal_places.filter(
            verification_state=Location.VerificationState.UNVERIFIED,
        )
        internal_places_already_verified = eligible_internal_places.filter(
            verification_state=Location.VerificationState.FIELD_VERIFIED,
        ).count()
        internal_places_skipped = all_internal_places.exclude(
            pk__in=eligible_internal_places.values("pk"),
        ).count()

        # 3. ENTRANCES (Active entrances of published places)
        all_entrances = Entrance.objects.all()
        eligible_entrances = all_entrances.filter(
            is_active=True,
            location__publication_status=Location.PublicationStatus.PUBLISHED,
            updated_at__lt=BASELINE_SNAPSHOT_CUTOFF,
            location__updated_at__lt=BASELINE_SNAPSHOT_CUTOFF,
        )
        entrances_to_verify = eligible_entrances.filter(
            verification_state=Location.VerificationState.UNVERIFIED,
        )
        entrances_already_verified = eligible_entrances.filter(
            verification_state=Location.VerificationState.FIELD_VERIFIED,
        ).count()
        entrances_skipped = all_entrances.exclude(pk__in=eligible_entrances.values("pk")).count()

        # 4. WALKABLE NODES (Active graph nodes)
        all_nodes = WalkableNode.objects.all()
        eligible_nodes = all_nodes.filter(
            is_active=True,
            updated_at__lt=BASELINE_SNAPSHOT_CUTOFF,
        )
        nodes_to_verify = eligible_nodes.filter(
            verification_state=VerificationState.UNVERIFIED,
        )
        nodes_already_verified = eligible_nodes.filter(
            verification_state=VerificationState.FIELD_VERIFIED,
        ).count()
        nodes_skipped = all_nodes.exclude(pk__in=eligible_nodes.values("pk")).count()

        # 5. WALKABLE SEGMENTS (Active graph segments)
        all_segments = WalkableSegment.objects.all()
        eligible_segments = all_segments.filter(
            is_active=True,
            updated_at__lt=BASELINE_SNAPSHOT_CUTOFF,
        )
        segments_to_verify = eligible_segments.filter(
            verification_state=VerificationState.UNVERIFIED,
        )
        segments_already_verified = eligible_segments.filter(
            verification_state=VerificationState.FIELD_VERIFIED,
        ).count()
        segments_skipped = all_segments.exclude(pk__in=eligible_segments.values("pk")).count()

        # 6. LEGACY LOCATION ANCHORS (Active, public, active-node records)
        all_location_anchors = LocationNetworkAnchor.objects.all()
        eligible_location_anchors = all_location_anchors.filter(
            is_active=True,
            location__publication_status=Location.PublicationStatus.PUBLISHED,
            node__is_active=True,
            updated_at__lt=BASELINE_SNAPSHOT_CUTOFF,
            location__updated_at__lt=BASELINE_SNAPSHOT_CUTOFF,
            node__updated_at__lt=BASELINE_SNAPSHOT_CUTOFF,
        )
        location_anchors_to_verify = eligible_location_anchors.filter(
            verification_state=VerificationState.UNVERIFIED,
        )
        location_anchors_already_verified = eligible_location_anchors.filter(
            verification_state=VerificationState.FIELD_VERIFIED,
        ).count()
        location_anchors_skipped = all_location_anchors.exclude(
            pk__in=eligible_location_anchors.values("pk"),
        ).count()

        # 7. ENTRANCE ANCHORS (Active records for eligible entrances/nodes)
        all_entrance_anchors = EntranceNetworkAnchor.objects.all()
        eligible_entrance_anchors = all_entrance_anchors.filter(
            is_active=True,
            entrance__in=eligible_entrances,
            node__is_active=True,
            updated_at__lt=BASELINE_SNAPSHOT_CUTOFF,
            node__updated_at__lt=BASELINE_SNAPSHOT_CUTOFF,
        )
        entrance_anchors_to_verify = eligible_entrance_anchors.filter(
            verification_state=VerificationState.UNVERIFIED,
        )
        entrance_anchors_already_verified = eligible_entrance_anchors.filter(
            verification_state=VerificationState.FIELD_VERIFIED,
        ).count()
        entrance_anchors_skipped = all_entrance_anchors.exclude(
            pk__in=eligible_entrance_anchors.values("pk"),
        ).count()

        # Report breakdown
        self.stdout.write("Entity Breakdown:")
        self.stdout.write(
            f"  Locations: {eligible_locations.count()} eligible, "
            f"{locations_already_verified} already verified, "
            f"{locations_to_verify.count()} would change, "
            f"{locations_skipped} skipped (unpublished or outside snapshot)"
        )
        self.stdout.write(
            f"  InternalPlaces: {eligible_internal_places.count()} eligible, "
            f"{internal_places_already_verified} already verified, "
            f"{internal_places_to_verify.count()} would change, "
            f"{internal_places_skipped} skipped (unpublished, ineligible parent, or outside snapshot)"
        )
        self.stdout.write(
            f"  Entrances: {eligible_entrances.count()} eligible, "
            f"{entrances_already_verified} already verified, "
            f"{entrances_to_verify.count()} would change, "
            f"{entrances_skipped} skipped (inactive, unpublished parent, or outside snapshot)"
        )
        self.stdout.write(
            f"  WalkableNodes: {eligible_nodes.count()} eligible, "
            f"{nodes_already_verified} already verified, "
            f"{nodes_to_verify.count()} would change, "
            f"{nodes_skipped} skipped (inactive or outside snapshot)"
        )
        self.stdout.write(
            f"  WalkableSegments: {eligible_segments.count()} eligible, "
            f"{segments_already_verified} already verified, "
            f"{segments_to_verify.count()} would change, "
            f"{segments_skipped} skipped (inactive or outside snapshot)"
        )
        self.stdout.write(
            f"  LocationNetworkAnchors: {eligible_location_anchors.count()} eligible, "
            f"{location_anchors_already_verified} already verified, "
            f"{location_anchors_to_verify.count()} would change, "
            f"{location_anchors_skipped} skipped (inactive, unpublished, inactive node, or outside snapshot)"
        )
        self.stdout.write(
            f"  EntranceNetworkAnchors: {eligible_entrance_anchors.count()} eligible, "
            f"{entrance_anchors_already_verified} already verified, "
            f"{entrance_anchors_to_verify.count()} would change, "
            f"{entrance_anchors_skipped} skipped (inactive, ineligible entrance/node, or outside snapshot)"
        )

        total_to_verify = (
            locations_to_verify.count()
            + internal_places_to_verify.count()
            + entrances_to_verify.count()
            + nodes_to_verify.count()
            + segments_to_verify.count()
            + location_anchors_to_verify.count()
            + entrance_anchors_to_verify.count()
        )

        self.stdout.write(f"\nTotal records to update: {total_to_verify}")

        candidate_groups = (
            ("Locations", locations_to_verify.order_by("name"), lambda item: item.name),
            ("InternalPlaces", internal_places_to_verify.select_related("location").order_by(
                "location__name", "name",
            ), lambda item: f"{item.location.name} / {item.name}"),
            ("Entrances", entrances_to_verify.select_related("location").order_by(
                "location__name", "name",
            ), lambda item: f"{item.location.name} / {item.name}"),
            ("WalkableNodes", nodes_to_verify.order_by("label", "id"), lambda item: item.display_label),
            ("WalkableSegments", segments_to_verify.order_by("label", "id"), lambda item: item.display_label),
            ("LocationNetworkAnchors", location_anchors_to_verify.select_related(
                "location", "node",
            ).order_by("location__name"), lambda item: f"{item.location.name} -> {item.node.display_label}"),
            ("EntranceNetworkAnchors", entrance_anchors_to_verify.select_related(
                "entrance__location", "node",
            ).order_by("entrance__location__name", "entrance__name"),
             lambda item: f"{item.entrance.location.name} / {item.entrance.name} -> {item.node.display_label}"),
        )
        self.stdout.write("\nCandidate records:")
        if total_to_verify:
            for group_name, queryset, describe in candidate_groups:
                candidates = list(queryset)
                if not candidates:
                    continue
                self.stdout.write(f"  {group_name}:")
                for item in candidates:
                    self.stdout.write(f"    - {describe(item)} [{item.pk}]")
        else:
            self.stdout.write("  None")

        if total_to_verify == 0:
            self.stdout.write(self.style.SUCCESS("\nAccepted map baseline is already fully FIELD_VERIFIED. Nothing to change."))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING("\n[DRY-RUN] No database modifications were made. Re-run with --apply to execute."))
            return

        # Perform atomic update
        with transaction.atomic():
            # Update Locations
            loc_count = locations_to_verify.update(
                verification_state=Location.VerificationState.FIELD_VERIFIED,
            )
            # Update Internal Places
            internal_count = internal_places_to_verify.update(
                verification_state=Location.VerificationState.FIELD_VERIFIED,
            )
            # Update Entrances
            ent_count = entrances_to_verify.update(
                verification_state=Location.VerificationState.FIELD_VERIFIED,
            )
            # Update both current anchor types.
            location_anchor_count = location_anchors_to_verify.update(
                verification_state=VerificationState.FIELD_VERIFIED,
            )
            entrance_anchor_count = entrance_anchors_to_verify.update(
                verification_state=VerificationState.FIELD_VERIFIED,
            )
            # Update WalkableNodes
            node_count = nodes_to_verify.update(
                verification_state=VerificationState.FIELD_VERIFIED,
            )
            # Update WalkableSegments and create audit records
            seg_list = list(segments_to_verify)
            for seg in seg_list:
                seg.verification_state = VerificationState.FIELD_VERIFIED
                seg.save(update_fields=("verification_state", "updated_at"))
                SegmentVerificationRecord.objects.create(
                    segment=seg,
                    action=SegmentVerificationRecord.Action.GRANTED,
                    geometry_revision=seg.geometry_revision,
                    geometry_fingerprint=seg.geometry_fingerprint,
                    actor=None,
                    reason=AUDIT_REASON,
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n[APPLIED] Successfully marked {loc_count} Locations, {ent_count} Entrances, "
                f"{internal_count} InternalPlaces, {node_count} Nodes, {len(seg_list)} Segments, "
                f"{location_anchor_count} LocationNetworkAnchors, and "
                f"{entrance_anchor_count} EntranceNetworkAnchors as FIELD_VERIFIED."
            )
        )
