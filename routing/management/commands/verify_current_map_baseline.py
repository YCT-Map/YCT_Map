"""Management command to transition the current accepted active map baseline

to FIELD_VERIFIED across Locations, Entrances, WalkableNodes, and WalkableSegments.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from locations.models import Entrance, Location
from routing.models import (EntranceNetworkAnchor, SegmentVerificationRecord,
                            VerificationState, WalkableNode, WalkableSegment)

AUDIT_REASON = "Owner-approved final map baseline"


class Command(BaseCommand):
    help = (
        "Mark the accepted current active map baseline (Locations, Entrances, "
        "WalkableNodes, and WalkableSegments) as FIELD_VERIFIED."
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

        # 1. LOCATIONS (Published active outdoor places)
        all_locations = Location.objects.all()
        eligible_locations = all_locations.filter(
            publication_status=Location.PublicationStatus.PUBLISHED,
        )
        locations_to_verify = eligible_locations.exclude(
            verification_state=Location.VerificationState.FIELD_VERIFIED,
        )
        locations_already_verified = eligible_locations.filter(
            verification_state=Location.VerificationState.FIELD_VERIFIED,
        ).count()
        locations_skipped = all_locations.exclude(
            publication_status=Location.PublicationStatus.PUBLISHED,
        ).count()

        # 2. ENTRANCES (Active entrances of published active places)
        all_entrances = Entrance.objects.all()
        eligible_entrances = all_entrances.filter(
            is_active=True,
            location__publication_status=Location.PublicationStatus.PUBLISHED,
        )
        entrances_to_verify = eligible_entrances.exclude(
            verification_state=Location.VerificationState.FIELD_VERIFIED,
        )
        entrances_already_verified = eligible_entrances.filter(
            verification_state=Location.VerificationState.FIELD_VERIFIED,
        ).count()
        entrances_skipped = all_entrances.exclude(
            is_active=True,
            location__publication_status=Location.PublicationStatus.PUBLISHED,
        ).count()

        # 3. WALKABLE NODES (Active graph nodes)
        all_nodes = WalkableNode.objects.all()
        eligible_nodes = all_nodes.filter(is_active=True)
        nodes_to_verify = eligible_nodes.exclude(
            verification_state=VerificationState.FIELD_VERIFIED,
        )
        nodes_already_verified = eligible_nodes.filter(
            verification_state=VerificationState.FIELD_VERIFIED,
        ).count()
        nodes_skipped = all_nodes.filter(is_active=False).count()

        # 4. WALKABLE SEGMENTS (Active graph segments)
        all_segments = WalkableSegment.objects.all()
        eligible_segments = all_segments.filter(is_active=True)
        segments_to_verify = eligible_segments.exclude(
            verification_state=VerificationState.FIELD_VERIFIED,
        )
        segments_already_verified = eligible_segments.filter(
            verification_state=VerificationState.FIELD_VERIFIED,
        ).count()
        segments_skipped = all_segments.filter(is_active=False).count()

        # Report breakdown
        self.stdout.write("Entity Breakdown:")
        self.stdout.write(
            f"  Locations: {eligible_locations.count()} eligible, "
            f"{locations_already_verified} already verified, "
            f"{locations_to_verify.count()} would change, "
            f"{locations_skipped} skipped (inactive/unpublished)"
        )
        self.stdout.write(
            f"  Entrances: {eligible_entrances.count()} eligible, "
            f"{entrances_already_verified} already verified, "
            f"{entrances_to_verify.count()} would change, "
            f"{entrances_skipped} skipped (inactive or unpublished parent)"
        )
        self.stdout.write(
            f"  WalkableNodes: {eligible_nodes.count()} eligible, "
            f"{nodes_already_verified} already verified, "
            f"{nodes_to_verify.count()} would change, "
            f"{nodes_skipped} skipped (inactive)"
        )
        self.stdout.write(
            f"  WalkableSegments: {eligible_segments.count()} eligible, "
            f"{segments_already_verified} already verified, "
            f"{segments_to_verify.count()} would change, "
            f"{segments_skipped} skipped (inactive)"
        )

        total_to_verify = (
            locations_to_verify.count()
            + entrances_to_verify.count()
            + nodes_to_verify.count()
            + segments_to_verify.count()
        )

        self.stdout.write(f"\nTotal records to update: {total_to_verify}")

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
            # Update Entrances
            ent_count = entrances_to_verify.update(
                verification_state=Location.VerificationState.FIELD_VERIFIED,
            )
            # Update Entrance Anchors for eligible entrances
            EntranceNetworkAnchor.objects.filter(
                is_active=True,
                entrance__in=eligible_entrances,
            ).update(
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
                f"{node_count} Nodes, and {len(seg_list)} Segments as FIELD_VERIFIED."
            )
        )
