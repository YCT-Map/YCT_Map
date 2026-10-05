"""Management command to deterministically assign stable human-facing numeric

node references (1, 2, 3...) and alphabetic segment references (A, B, C... Z, AA, AB...).
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from routing.labels import integer_to_segment_code, is_valid_node_label, is_valid_segment_label
from routing.models import WalkableNode, WalkableSegment


class Command(BaseCommand):
    help = (
        "Assign clean, stable human-facing numeric labels (1, 2, 3...) to nodes "
        "and alphabetic labels (A, B, C... Z, AA, AB...) to segments."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report planned label assignments without writing to the database.",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Persist label assignments to the database.",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run")
        apply_changes = options.get("apply")

        # Default to dry-run unless --apply is explicitly specified
        if not apply_changes:
            dry_run = True

        self.stdout.write(self.style.MIGRATE_HEADING("=== Graph Display Labels Normalization ==="))
        mode_str = "APPLY" if apply_changes else "DRY-RUN (read-only)"
        self.stdout.write(f"Mode: {mode_str}\n")

        # --- NODES ---
        nodes = list(WalkableNode.objects.order_by("created_at", "source_reference", "id"))
        total_nodes = len(nodes)

        # Check current validity and idempotency
        all_nodes_valid = (
            total_nodes > 0
            and all(is_valid_node_label(n.label) for n in nodes)
            and len({n.label for n in nodes}) == total_nodes
        )

        nodes_to_update = []
        if all_nodes_valid:
            self.stdout.write(self.style.SUCCESS(f"Nodes: All {total_nodes} nodes already have valid, unique numeric labels (1..N). No changes required."))
        else:
            self.stdout.write(f"Nodes: Normalizing {total_nodes} node labels to numeric sequence 1..{total_nodes}...")
            for idx, node in enumerate(nodes, start=1):
                expected_label = str(idx)
                if node.label != expected_label:
                    nodes_to_update.append((node, expected_label))

        # --- SEGMENTS ---
        segments = list(WalkableSegment.objects.order_by("created_at", "source_reference", "id"))
        total_segments = len(segments)

        all_segments_valid = (
            total_segments > 0
            and all(is_valid_segment_label(s.label) for s in segments)
            and len({s.label for s in segments}) == total_segments
        )

        segments_to_update = []
        if all_segments_valid:
            self.stdout.write(self.style.SUCCESS(f"Segments: All {total_segments} segments already have valid, unique alphabetic labels (A..ZZ). No changes required."))
        else:
            self.stdout.write(f"Segments: Normalizing {total_segments} segment labels to alphabetic sequence A..{integer_to_segment_code(total_segments)}...")
            for idx, segment in enumerate(segments, start=1):
                expected_label = integer_to_segment_code(idx)
                if segment.label != expected_label:
                    segments_to_update.append((segment, expected_label))

        self.stdout.write("\nSummary:")
        self.stdout.write(f"  Nodes: {total_nodes} total, {len(nodes_to_update)} to update, {total_nodes - len(nodes_to_update)} unchanged")
        self.stdout.write(f"  Segments: {total_segments} total, {len(segments_to_update)} to update, {total_segments - len(segments_to_update)} unchanged")

        if not nodes_to_update and not segments_to_update:
            self.stdout.write(self.style.SUCCESS("\nGraph is already fully normalized. No database writes needed."))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING("\n[DRY-RUN] No database modifications were made. Re-run with --apply to persist changes."))
            return

        # Perform atomic update
        with transaction.atomic():
            for node, new_label in nodes_to_update:
                update_fields = ["label", "updated_at"]
                if not node.source_reference and node.label and not node.label.isdigit():
                    node.source_reference = node.label
                    update_fields.append("source_reference")
                node.label = new_label
                node.save(update_fields=tuple(update_fields))

            for segment, new_label in segments_to_update:
                update_fields = ["label", "updated_at"]
                if not segment.source_reference and segment.label and not is_valid_segment_label(segment.label):
                    segment.source_reference = segment.label
                    update_fields.append("source_reference")
                segment.label = new_label
                segment.save(update_fields=tuple(update_fields))

        self.stdout.write(self.style.SUCCESS(f"\n[APPLIED] Successfully updated {len(nodes_to_update)} nodes and {len(segments_to_update)} segments."))
