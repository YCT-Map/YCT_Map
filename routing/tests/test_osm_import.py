from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from locations.models import Location
from routing.models import LocationNetworkAnchor, SourceType, VerificationState, WalkableNode, WalkableSegment
from routing.osm_import import build_records, load_json


SNAPSHOT = settings.BASE_DIR / "routing/data/osm/yabatech_highways_2026-09-18.overpass.json"
REVIEW = settings.BASE_DIR / "routing/data/osm/yabatech_review.json"
BOUNDARY = settings.BASE_DIR / "static/yct_map/data/yabatech-campus-boundary.geojson"


class OsmImportTransformationTests(TestCase):
    def test_reviewed_snapshot_builds_deterministic_unconnected_decision_topology(self):
        first = build_records(load_json(SNAPSHOT), load_json(REVIEW), load_json(BOUNDARY))
        second = build_records(load_json(SNAPSHOT), load_json(REVIEW), load_json(BOUNDARY))

        self.assertEqual(first, second)
        self.assertGreaterEqual(len(first["nodes"]), 43)
        self.assertGreaterEqual(len(first["segments"]), 50)
        self.assertEqual(first["rejected"], [])
        references = {node["source_reference"] for node in first["nodes"]}
        self.assertTrue(set(load_json(REVIEW)["location_anchors"].values()).issubset(references))
        self.assertTrue(all(segment["source_reference"].startswith("way/") for segment in first["segments"]))

    def test_restricted_way_is_rejected(self):
        snapshot = {"elements": [{
            "type": "way", "id": 1, "nodes": [1, 2],
            "geometry": [{"lon": 3.374, "lat": 6.518}, {"lon": 3.375, "lat": 6.518}],
            "tags": {"highway": "footway", "foot": "no"},
        }]}
        review = {"approved_way_ids": [1], "location_anchors": {}}

        records = build_records(snapshot, review, load_json(BOUNDARY))

        self.assertEqual(records["segments"], [])
        self.assertEqual(records["rejected"], [{"way_id": 1, "reason": "access restriction"}])


class OsmImportCommandTests(TestCase):
    fixtures = ["demo_locations.json"]

    def test_import_replaces_synthetic_network_and_anchors_every_demo_location(self):
        call_command("import_osm_walkable_network", snapshot=str(SNAPSHOT), review=str(REVIEW), boundary=str(BOUNDARY), apply=True, verbosity=0)

        self.assertGreaterEqual(WalkableNode.objects.count(), 43)
        self.assertGreaterEqual(WalkableSegment.objects.count(), 50)
        self.assertEqual(LocationNetworkAnchor.objects.count(), 6)
        self.assertEqual(Location.objects.filter(network_anchor__is_active=True).count(), 6)
        self.assertFalse(WalkableNode.objects.exclude(source_type=SourceType.OSM).exists())
        self.assertFalse(WalkableSegment.objects.exclude(source_type=SourceType.OSM).exists())
        self.assertFalse(WalkableSegment.objects.exclude(verification_state=VerificationState.UNVERIFIED).exists())
        self.assertTrue(WalkableSegment.objects.filter(source_version__isnull=False, source_timestamp__isnull=False).exists())
