import json
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from locations.models import Location, LocationAlias


class LocationModelTests(TestCase):
    def make_location(self, **overrides):
        values = {
            "name": "DEMO — Test Building",
            "category": Location.Category.BUILDING,
            "description": "Synthetic test destination.",
            "entrance_latitude": Decimal("6.518570"),
            "entrance_longitude": Decimal("3.374240"),
            "verification_state": Location.VerificationState.DEMO,
        }
        values.update(overrides)
        return Location.objects.create(**values)

    def test_controlled_choices_reject_unknown_values_during_validation(self):
        location = self.make_location(category="anything")

        with self.assertRaises(ValidationError):
            location.full_clean()

    def test_coordinate_validation_rejects_out_of_range_values(self):
        location = self.make_location(entrance_latitude=Decimal("91.000000"))

        with self.assertRaises(ValidationError):
            location.full_clean()

    def test_aliases_belong_to_one_location(self):
        location = self.make_location()
        alias = LocationAlias.objects.create(location=location, name="DEMO — Lecture Block")

        self.assertEqual(list(location.aliases.all()), [alias])


class LocationEndpointTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.library = Location.objects.create(
            name="DEMO — Library",
            category=Location.Category.LIBRARY,
            description="Synthetic library.",
            entrance_latitude=Decimal("6.518720"),
            entrance_longitude=Decimal("3.374110"),
            verification_state=Location.VerificationState.DEMO,
        )
        LocationAlias.objects.create(location=cls.library, name="DEMO — Reading Room")
        cls.cafe = Location.objects.create(
            name="DEMO — Café",
            category=Location.Category.FOOD,
            description="Synthetic café.",
            entrance_latitude=Decimal("6.518300"),
            entrance_longitude=Decimal("3.374780"),
            verification_state=Location.VerificationState.DEMO,
        )
        Location.objects.create(
            name="DEMO — Hidden",
            category=Location.Category.OFFICE,
            entrance_latitude=Decimal("6.518000"),
            entrance_longitude=Decimal("3.374000"),
            verification_state=Location.VerificationState.DEMO,
            is_active=False,
        )

    @property
    def url(self):
        return reverse("locations:collection")

    def test_endpoint_returns_explicit_geojson_contract(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["type"], "FeatureCollection")
        self.assertEqual(payload["meta"]["count"], 2)
        feature = next(item for item in payload["features"] if item["properties"]["name"] == "DEMO — Library")
        self.assertEqual(feature["geometry"]["type"], "Point")
        self.assertEqual(
            set(feature["properties"]),
            {
                "id",
                "name",
                "category",
                "category_label",
                "description",
                "verification_state",
                "verification_label",
                "aliases",
            },
        )
        self.assertNotIn("created_at", feature["properties"])

    def test_search_is_case_insensitive_and_partial(self):
        response = self.client.get(self.url, {"q": "lIbRa"})

        self.assertEqual(response.json()["meta"]["count"], 1)
        self.assertEqual(response.json()["features"][0]["properties"]["name"], "DEMO — Library")

    def test_search_matches_alias(self):
        response = self.client.get(self.url, {"q": "reading room"})

        self.assertEqual(response.json()["meta"]["count"], 1)
        self.assertEqual(response.json()["features"][0]["properties"]["name"], "DEMO — Library")

    def test_category_filter_is_optional(self):
        response = self.client.get(self.url, {"category": Location.Category.FOOD})

        self.assertEqual(response.json()["meta"]["count"], 1)
        self.assertEqual(response.json()["features"][0]["properties"]["name"], "DEMO — Café")

    def test_no_result_returns_empty_feature_collection(self):
        response = self.client.get(self.url, {"q": "not present"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["features"], [])

    def test_invalid_category_and_long_query_are_rejected(self):
        invalid_category = self.client.get(self.url, {"category": "arbitrary"})
        long_query = self.client.get(self.url, {"q": "x" * 101})

        self.assertEqual(invalid_category.status_code, 400)
        self.assertEqual(long_query.status_code, 400)

    def test_endpoint_is_read_only(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 405)


class MapPageTests(TestCase):
    def test_map_page_contains_approved_map_configuration(self):
        response = self.client.get(reverse("locations:map"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "https://tiles.openfreemap.org/styles/liberty")
        self.assertContains(response, 'data-centre-longitude="3.37424"')
        self.assertContains(response, 'data-centre-latitude="6.51857"')
        self.assertContains(response, "yct_map/data/yabatech-campus-boundary.geojson")
        self.assertContains(response, "DEMO DATA")

    def test_campus_orientation_boundary_is_the_approved_osm_polygon(self):
        boundary_path = settings.BASE_DIR / "static/yct_map/data/yabatech-campus-boundary.geojson"
        boundary = json.loads(boundary_path.read_text(encoding="utf-8"))

        self.assertEqual(boundary["type"], "FeatureCollection")
        self.assertEqual(boundary["metadata"]["osm_type"], "way")
        self.assertEqual(boundary["metadata"]["osm_id"], 671850885)
        self.assertEqual(boundary["features"][0]["geometry"]["type"], "Polygon")
        self.assertEqual(
            boundary["features"][0]["properties"]["data_role"],
            "orientation_boundary",
        )

        ring = boundary["features"][0]["geometry"]["coordinates"][0]
        self.assertEqual(ring[0], ring[-1])
        self.assertGreaterEqual(len(ring), 4)
        self.assertNotIn("verification_state", boundary["features"][0]["properties"])


class DemoFixtureTests(TestCase):
    def test_fixture_is_explicitly_demo_only(self):
        call_command("loaddata", "demo_locations", verbosity=0)

        locations = Location.objects.all()
        self.assertEqual(locations.count(), 6)
        self.assertTrue(all(item.name.startswith("DEMO —") for item in locations))
        self.assertTrue(
            all(item.verification_state == Location.VerificationState.DEMO for item in locations)
        )
