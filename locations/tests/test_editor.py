from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.test import Client
from django.urls import reverse

from locations.models import Category, Location, LocationAlias


class EditorAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.editor = get_user_model().objects.create_user("editor", password="Strong-test-password-42")
        cls.editor.groups.add(Group.objects.get(name="Editor"))
        cls.admin = get_user_model().objects.create_superuser(
            "administrator", "admin@example.test", "Strong-test-password-42"
        )

    def test_anonymous_editor_access_redirects_to_login(self):
        response = self.client.get(reverse("editor:dashboard"))
        self.assertRedirects(response, f"{reverse('editor:login')}?next={reverse('editor:dashboard')}")

    def test_login_success_failure_and_safe_next(self):
        failed = self.client.post(reverse("editor:login"), {"username": "editor", "password": "wrong"})
        self.assertEqual(failed.status_code, 200)
        success = self.client.post(
            f"{reverse('editor:login')}?next=https://example.com/steal",
            {"username": "editor", "password": "Strong-test-password-42", "next": "https://example.com/steal"},
        )
        self.assertRedirects(success, reverse("editor:dashboard"), fetch_redirect_response=False)

    def test_logout_is_post_only(self):
        self.client.force_login(self.editor)
        self.assertEqual(self.client.get(reverse("editor:logout")).status_code, 405)
        response = self.client.post(reverse("editor:logout"))
        self.assertRedirects(response, reverse("editor:login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_inactive_user_cannot_log_in(self):
        self.editor.is_active = False
        self.editor.save(update_fields=("is_active",))
        response = self.client.post(
            reverse("editor:login"),
            {"username": "editor", "password": "Strong-test-password-42"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_editor_permissions_are_least_privilege(self):
        self.assertTrue(self.editor.has_perm("locations.add_location"))
        self.assertTrue(self.editor.has_perm("locations.change_location"))
        self.assertTrue(self.editor.has_perm("locations.view_category"))
        self.assertFalse(self.editor.has_perm("locations.delete_location"))
        self.assertFalse(self.editor.has_perm("locations.add_category"))
        self.assertFalse(self.editor.has_perm("auth.add_user"))
        self.assertFalse(self.editor.is_staff)

    def test_editor_and_administrator_can_open_editor(self):
        for user in (self.editor, self.admin):
            self.client.force_login(user)
            self.assertEqual(self.client.get(reverse("editor:dashboard")).status_code, 200)
            self.client.logout()

    def test_user_without_permission_is_forbidden(self):
        user = get_user_model().objects.create_user("viewer", password="Strong-test-password-42")
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("editor:place-list")).status_code, 403)
        self.assertEqual(self.client.post(reverse("editor:place-create"), {}).status_code, 403)

    def test_editor_state_changes_require_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.editor)
        self.assertEqual(csrf_client.post(reverse("editor:logout")).status_code, 403)
        self.assertEqual(csrf_client.post(reverse("editor:place-create"), {}).status_code, 403)


class EditorPlaceCrudTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.editor = get_user_model().objects.create_user("editor", password="Strong-test-password-42")
        cls.editor.groups.add(Group.objects.get(name="Editor"))

    def setUp(self):
        self.client.force_login(self.editor)

    def payload(self, **overrides):
        values = {
            "name": "TEST — Student Centre",
            "description": "Synthetic editor workflow record.",
            "place_type": Location.PlaceType.BUILDING,
            "categories": ["academic", "student-services"],
            "publication_status": Location.PublicationStatus.DRAFT,
            "aliases-TOTAL_FORMS": "2",
            "aliases-INITIAL_FORMS": "0",
            "aliases-MIN_NUM_FORMS": "0",
            "aliases-MAX_NUM_FORMS": "1000",
            "aliases-0-name": "TSC",
            "aliases-0-alias_kind": LocationAlias.Kind.ABBREVIATION,
            "aliases-1-name": "Student hub",
            "aliases-1-alias_kind": LocationAlias.Kind.COMMON_NAME,
        }
        values.update(overrides)
        return values

    def test_create_draft_with_multiple_categories_aliases_and_audit_actor(self):
        response = self.client.post(reverse("editor:place-create"), self.payload())
        location = Location.objects.get(name="TEST — Student Centre")
        self.assertRedirects(response, reverse("editor:place-detail", args=(location.id,)))
        self.assertEqual(location.publication_status, Location.PublicationStatus.DRAFT)
        self.assertEqual(location.verification_state, Location.VerificationState.UNVERIFIED)
        self.assertIsNone(location.representative_latitude)
        self.assertEqual(set(location.categories.values_list("slug", flat=True)), {"academic", "student-services"})
        self.assertEqual(set(location.aliases.values_list("alias_kind", flat=True)), {"ABBREVIATION", "COMMON_NAME"})
        self.assertEqual(location.created_by, self.editor)
        self.assertEqual(location.updated_by, self.editor)

    def test_publication_without_point_is_rejected(self):
        response = self.client.post(
            reverse("editor:place-create"),
            self.payload(publication_status=Location.PublicationStatus.PUBLISHED),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "representative point is required")
        self.assertFalse(Location.objects.filter(name="TEST — Student Centre").exists())

    def test_edit_archive_and_reactivate(self):
        location = Location.objects.create(
            name="TEST — Existing",
            place_type=Location.PlaceType.FACILITY,
            publication_status=Location.PublicationStatus.DRAFT,
        )
        edit_payload = self.payload(
            name="TEST — Updated",
            place_type=Location.PlaceType.CAMPUS_AREA,
            **{
                "aliases-INITIAL_FORMS": "0",
                "aliases-0-name": "Updated place",
                "aliases-1-name": "",
                "aliases-1-alias_kind": "",
            },
        )
        response = self.client.post(reverse("editor:place-detail", args=(location.id,)), edit_payload)
        self.assertEqual(
            response.status_code,
            302,
            (response.context["form"].errors, response.context["aliases"].errors) if response.context else None,
        )
        location.refresh_from_db()
        self.assertEqual(location.name, "TEST — Updated")
        self.assertEqual(location.updated_by, self.editor)

        self.client.post(reverse("editor:place-archive", args=(location.id,)))
        location.refresh_from_db()
        self.assertEqual(location.publication_status, Location.PublicationStatus.ARCHIVED)
        self.assertFalse(location.is_active)

        self.client.post(
            reverse("editor:place-reactivate", args=(location.id,)),
            {"publication_status": Location.PublicationStatus.DRAFT},
        )
        location.refresh_from_db()
        self.assertEqual(location.publication_status, Location.PublicationStatus.DRAFT)

    def test_alias_duplicates_are_rejected_within_place(self):
        response = self.client.post(
            reverse("editor:place-create"),
            self.payload(**{"aliases-1-name": " tsc ", "aliases-1-alias_kind": LocationAlias.Kind.CODE}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already used for this place")

    def test_same_alias_is_allowed_for_different_places(self):
        first = Location.objects.create(name="First", place_type=Location.PlaceType.BUILDING)
        second = Location.objects.create(name="Second", place_type=Location.PlaceType.BUILDING)
        LocationAlias.objects.create(location=first, name="Shared", alias_kind=LocationAlias.Kind.CODE)
        alias = LocationAlias(location=second, name="Shared", alias_kind=LocationAlias.Kind.CODE)
        alias.full_clean()

    def test_direct_archive_requires_change_permission(self):
        location = Location.objects.create(name="Protected", place_type=Location.PlaceType.BUILDING)
        view_only = get_user_model().objects.create_user("view-only", password="Strong-test-password-42")
        self.client.force_login(view_only)
        self.assertEqual(self.client.post(reverse("editor:place-archive", args=(location.id,))).status_code, 403)


class CampusPlaceMigrationResultTests(TestCase):
    def test_controlled_taxonomy_was_seeded(self):
        self.assertEqual(Category.objects.count(), 12)
        self.assertEqual(Category.objects.get(slug="medical").legacy_filter, "health")

    def test_fixture_preserves_demo_ids_relationships_and_backfilled_fields(self):
        from django.core.management import call_command

        call_command("loaddata", "demo_locations", verbosity=0)
        expected_ids = {f"10000000-0000-4000-8000-{index:012d}" for index in range(1, 7)}
        locations = Location.objects.filter(id__in=expected_ids)
        self.assertEqual({str(item.id) for item in locations}, expected_ids)
        self.assertTrue(all(item.publication_status == Location.PublicationStatus.PUBLISHED for item in locations))
        self.assertTrue(all(item.verification_state == Location.VerificationState.DEMO for item in locations))
        self.assertTrue(all(item.has_representative_point for item in locations))
        self.assertEqual(LocationAlias.objects.filter(location__in=locations).count(), 4)
