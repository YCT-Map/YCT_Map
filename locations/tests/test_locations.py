import json
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from locations.models import Category, Location, LocationAlias


class LocationModelTests(TestCase):
    def make_location(self, **overrides):
        values = {
            "name": "DEMO — Test Building",
            "category": Location.Category.BUILDING,
            "description": "Synthetic test destination.",
            "entrance_latitude": Decimal("6.518570"),
            "entrance_longitude": Decimal("3.374240"),
            "representative_latitude": Decimal("6.518570"),
            "representative_longitude": Decimal("3.374240"),
            "publication_status": Location.PublicationStatus.PUBLISHED,
            "is_active": True,
            "verification_state": Location.VerificationState.DEMO,
        }
        values.update(overrides)
        return Location.objects.create(**values)

    def test_controlled_choices_reject_unknown_values_during_validation(self):
        location = self.make_location(category="anything")

        with self.assertRaises(ValidationError):
            location.full_clean()

    def test_checkpoint_defaults_false_and_is_independent_of_other_states(self):
        location = Location(name="Campus landmark")
        self.assertFalse(location.is_checkpoint)
        location.is_checkpoint = True
        location.publication_status = Location.PublicationStatus.DRAFT
        location.verification_state = Location.VerificationState.UNVERIFIED
        self.assertTrue(location.is_checkpoint)

    def test_coordinate_validation_rejects_out_of_range_values(self):
        location = self.make_location(entrance_latitude=Decimal("91.000000"))

        with self.assertRaises(ValidationError):
            location.full_clean()

    def test_aliases_belong_to_one_location(self):
        location = self.make_location()
        alias = LocationAlias.objects.create(location=location, name="DEMO — Lecture Block")

        self.assertEqual(list(location.aliases.all()), [alias])

    def test_draft_can_omit_representative_point(self):
        location = self.make_location(
            publication_status=Location.PublicationStatus.DRAFT,
            representative_latitude=None,
            representative_longitude=None,
        )
        location.full_clean()

    def test_published_place_requires_representative_point(self):
        location = self.make_location(representative_latitude=None, representative_longitude=None)
        with self.assertRaises(ValidationError):
            location.full_clean()

    def test_alias_collision_is_local_to_place_and_case_insensitive(self):
        first = self.make_location(name="First")
        second = self.make_location(name="Second")
        LocationAlias.objects.create(location=first, name="NASB")
        duplicate = LocationAlias(location=first, name=" nasb ")
        with self.assertRaises(ValidationError):
            duplicate.full_clean()
        allowed = LocationAlias(location=second, name="NASB", alias_kind=LocationAlias.Kind.CODE)
        allowed.full_clean()


class LocationEndpointTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.library = Location.objects.create(
            name="DEMO — Library",
            category=Location.Category.LIBRARY,
            description="Synthetic library.",
            entrance_latitude=Decimal("6.518720"),
            entrance_longitude=Decimal("3.374110"),
            representative_latitude=Decimal("6.518720"),
            representative_longitude=Decimal("3.374110"),
            publication_status=Location.PublicationStatus.PUBLISHED,
            is_active=True,
            verification_state=Location.VerificationState.DEMO,
        )
        LocationAlias.objects.create(location=cls.library, name="DEMO — Reading Room")
        cls.cafe = Location.objects.create(
            name="DEMO — Café",
            category=Location.Category.FOOD,
            description="Synthetic café.",
            entrance_latitude=Decimal("6.518300"),
            entrance_longitude=Decimal("3.374780"),
            representative_latitude=Decimal("6.518300"),
            representative_longitude=Decimal("3.374780"),
            publication_status=Location.PublicationStatus.PUBLISHED,
            is_active=True,
            verification_state=Location.VerificationState.DEMO,
        )
        Location.objects.create(
            name="DEMO — Hidden",
            category=Location.Category.OFFICE,
            entrance_latitude=Decimal("6.518000"),
            entrance_longitude=Decimal("3.374000"),
            verification_state=Location.VerificationState.DEMO,
            publication_status=Location.PublicationStatus.ARCHIVED,
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
                "is_checkpoint",
                "aliases",
                "categories",
                "place_type",
                "place_type_label",
                "routing_available",
                "routing_unavailable_reason",
                "destination_key",
                "destination_type",
                "places_inside_count",
            },
        )
        self.assertNotIn("created_at", feature["properties"])
        self.assertIs(feature["properties"]["is_checkpoint"], False)

    def test_checkpoint_is_explicit_in_public_geojson(self):
        self.library.is_checkpoint = True
        self.library.save(update_fields=("is_checkpoint",))
        feature = next(item for item in self.client.get(self.url).json()["features"]
                       if item["properties"]["id"] == str(self.library.id))
        self.assertIs(feature["properties"]["is_checkpoint"], True)

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

    def test_draft_is_excluded_even_if_legacy_active_flag_is_true(self):
        Location.objects.create(
            name="Draft place",
            category=Location.Category.BUILDING,
            publication_status=Location.PublicationStatus.DRAFT,
            representative_latitude=Decimal("6.518000"),
            representative_longitude=Decimal("3.374000"),
            is_active=True,
        )
        names = [item["properties"]["name"] for item in self.client.get(self.url).json()["features"]]
        self.assertNotIn("Draft place", names)

    def test_endpoint_is_read_only(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 405)


class MapPageTests(TestCase):
    def test_map_page_contains_approved_map_configuration(self):
        response = self.client.get(reverse("locations:map"))
        asset_version = "system-closeout-3"

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "https://tiles.openfreemap.org/styles/liberty")
        self.assertContains(response, 'data-centre-longitude="3.37424"')
        self.assertContains(response, 'data-centre-latitude="6.51857"')
        self.assertContains(response, "yct_map/data/yabatech-campus-boundary.geojson")
        self.assertNotContains(response, 'class="dataset-badge"')
        self.assertContains(response, "Some campus locations and walking paths may still be undergoing field verification.")
        self.assertContains(response, 'data-route-url="/api/routes/"')
        self.assertContains(response, 'id="destination-directions"')
        self.assertContains(response, 'id="user-route-panel"')
        self.assertContains(response, 'id="user-route-origin-options"')
        self.assertContains(response, 'id="user-route-origin-live"')
        self.assertContains(response, 'id="user-route-mapped-origins"')
        self.assertNotContains(response, '<select id="user-route-origin"')
        self.assertContains(response, f"app.js?v={asset_version}")
        self.assertContains(response, f"app.css?v={asset_version}")
        self.assertContains(response, 'data-contribution-url="/api/contributions/"')
        self.assertContains(response, 'id="contribution-panel"')
        self.assertContains(response, 'data-live-route-url="/api/routes/from-position/"')
        self.assertContains(response, 'id="user-location-controls"')
        self.assertContains(response, 'id="locate-me"')
        self.assertContains(response, 'id="recenter-me"')
        self.assertNotContains(response, 'id="follow-direction"')
        self.assertNotContains(response, 'id="north-up"')
        self.assertContains(response, 'id="direction-status"')
        self.assertContains(response, 'id="stop-location"')
        self.assertContains(response, "Location is optional and stays on this device.")
        self.assertContains(response, "yct_map/images/yct-map-logo.png", count=3)
        self.assertContains(response, 'class="brand-logo"')
        self.assertNotContains(response, "A* route inspection")

    def test_current_modules_use_the_same_cache_version(self):
        app_path = settings.BASE_DIR / "static/yct_map/js/app.js"
        app_source = app_path.read_text(encoding="utf-8")
        asset_version = "system-closeout-3"

        for module in (
            "api.js",
            "destination-panel.js",
            "map.js",
            "search.js",
            "route-inspector.js",
            "user-navigation.js",
            "contributions.js",
        ):
            self.assertIn(f'{module}?v={asset_version}', app_source)

        self.assertIn(f'user-location.js?v={asset_version}', app_source)
        self.assertIn(f'disclosure-menu.js?v={asset_version}', app_source)

        user_location_source = (
            settings.BASE_DIR / "static/yct_map/js/user-location.js"
        ).read_text(encoding="utf-8")
        self.assertIn(f"location-filter.js?v={asset_version}", user_location_source)
        self.assertIn(f"geolocation.js?v={asset_version}", user_location_source)
        self.assertIn(f"device-orientation.js?v={asset_version}", user_location_source)

        for relative_path in (
            "templates/editor/base.html",
            "templates/editor/place_form.html",
            "templates/editor/entrance_form.html",
            "templates/editor/path_list.html",
            "templates/editor/node_form.html",
            "templates/editor/segment_form.html",
            "templates/editor/segment_split.html",
            "templates/editor/survey_detail.html",
            "static/yct_map/js/editor-place-map.js",
            "static/yct_map/js/editor-entrance-map.js",
            "static/yct_map/js/location-capture.js",
            "static/yct_map/js/map.js",
            "static/yct_map/js/off-route.js",
            "static/yct_map/js/user-navigation.js",
        ):
            source = (settings.BASE_DIR / relative_path).read_text(encoding="utf-8")
            self.assertNotRegex(source, rf"\?v=(?!{asset_version})[A-Za-z0-9._-]+", relative_path)

    def test_map_has_no_global_badge_while_record_verification_remains_public(self):
        location = Location.objects.create(
            name="Unverified place",
            publication_status=Location.PublicationStatus.PUBLISHED,
            verification_state=Location.VerificationState.UNVERIFIED,
            representative_latitude=Decimal("6.518000"),
            representative_longitude=Decimal("3.374000"),
        )
        map_response = self.client.get(reverse("locations:map"))
        self.assertNotContains(map_response, "UNVERIFIED DATA")
        self.assertNotContains(map_response, 'class="dataset-badge"')
        feature = self.client.get(reverse("locations:collection")).json()["features"][0]
        self.assertEqual(feature["properties"]["verification_state"], "UNVERIFIED")

        location.verification_state = Location.VerificationState.DEMO
        location.save(update_fields=("verification_state",))
        map_response = self.client.get(reverse("locations:map"))
        self.assertNotContains(map_response, "DEMO DATA")
        feature = self.client.get(reverse("locations:collection")).json()["features"][0]
        self.assertEqual(feature["properties"]["verification_state"], "DEMO")
        self.assertEqual(feature["properties"]["verification_label"], "Demo")

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
        self.assertTrue(all(item.publication_status == Location.PublicationStatus.PUBLISHED for item in locations))
        self.assertTrue(all(item.has_representative_point for item in locations))
        self.assertTrue(all(item.categories.exists() for item in locations))
        self.assertEqual(Category.objects.count(), 12)
