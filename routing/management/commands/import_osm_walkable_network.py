from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from locations.models import Location
from routing.models import LocationNetworkAnchor, SourceType, VerificationState, WalkableNode, WalkableSegment
from routing.osm_import import build_records, load_json


class Command(BaseCommand):
    help = "Import a reviewed OSM snapshot as YCT Map-owned UNVERIFIED routing data."

    def add_arguments(self, parser):
        parser.add_argument("--snapshot", required=True)
        parser.add_argument("--review", required=True)
        parser.add_argument("--boundary", default="static/yct_map/data/yabatech-campus-boundary.geojson")
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        snapshot = load_json(options["snapshot"])
        review = load_json(options["review"])
        records = build_records(snapshot, review, load_json(options["boundary"]))
        self.stdout.write(f"Prepared {len(records['nodes'])} nodes and {len(records['segments'])} segments; rejected {len(records['rejected'])} ways.")
        if not options["apply"]:
            self.stdout.write("Dry run only; no database records changed.")
            return

        by_reference = {}
        with transaction.atomic():
            LocationNetworkAnchor.objects.all().delete()
            WalkableSegment.objects.all().delete()
            WalkableNode.objects.all().delete()
            for record in records["nodes"]:
                node = WalkableNode(
                    id=record["id"], label=record["label"], longitude=record["longitude"], latitude=record["latitude"],
                    verification_state=VerificationState.UNVERIFIED, source_type=SourceType.OSM,
                    source_reference=record["source_reference"], is_active=True,
                )
                node.full_clean()
                node.save()
                by_reference[node.source_reference] = node
            for record in records["segments"]:
                segment = WalkableSegment(
                    id=record["id"], label=record["label"], start_node=by_reference[record["start_reference"]],
                    end_node=by_reference[record["end_reference"]], geometry=record["geometry"],
                    is_bidirectional=record["is_bidirectional"], verification_state=VerificationState.UNVERIFIED,
                    source_type=SourceType.OSM, source_reference=record["source_reference"],
                    source_version=record["source_version"], source_timestamp=record["source_timestamp"], is_active=True,
                )
                segment.full_clean()
                segment.save()
            for location_id, node_reference in review.get("location_anchors", {}).items():
                try:
                    location = Location.objects.get(id=location_id, is_active=True)
                    node = by_reference[node_reference]
                except (Location.DoesNotExist, KeyError) as error:
                    raise CommandError(f"Invalid reviewed anchor {location_id} -> {node_reference}") from error
                LocationNetworkAnchor.objects.create(
                    location=location, node=node, verification_state=VerificationState.UNVERIFIED, is_active=True,
                )
        self.stdout.write(self.style.SUCCESS(f"Imported {len(records['nodes'])} nodes, {len(records['segments'])} segments and {len(review.get('location_anchors', {}))} anchors."))
