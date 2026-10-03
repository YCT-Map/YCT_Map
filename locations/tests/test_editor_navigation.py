import json
import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client, TestCase
from django.urls import reverse

from contributions.models import Contribution
from locations.models import Entrance, Floor, InternalPlace, Location
from routing.models import (PathSurvey, SourceType, VerificationState,
                            WalkableNode, WalkableSegment)


class EditorMutationNavigationTests(TestCase):
    """Browser-facing editor mutations must finish on stable GET pages."""

    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_superuser(
            "navigation-owner", "owner@example.test", "Strong-test-password-42",
        )

    def setUp(self):
        self.client.force_login(self.owner)

    def place_payload(self, name="TEST — Navigation place", **overrides):
        payload = {
            "name": name,
            "description": "Editor navigation regression record.",
            "place_type": Location.PlaceType.BUILDING,
            "publication_status": Location.PublicationStatus.DRAFT,
            "aliases-TOTAL_FORMS": "0",
            "aliases-INITIAL_FORMS": "0",
            "aliases-MIN_NUM_FORMS": "0",
            "aliases-MAX_NUM_FORMS": "1000",
        }
        payload.update(overrides)
        return payload

    @staticmethod
    def entrance_payload(**overrides):
        payload = {
            "name": "Main entrance",
            "entrance_type": Entrance.Type.MAIN,
            "latitude": "6.518000",
            "longitude": "3.374000",
            "is_primary": "on",
            "is_active": "on",
        }
        payload.update(overrides)
        return payload

    def assert_stable_get_redirect(self, response, expected_url):
        self.assertIn(response.status_code, (302, 303))
        self.assertEqual(response.headers["Location"], expected_url)
        self.assertEqual(self.client.get(expected_url).status_code, 200)
        self.assertEqual(self.client.get(expected_url).status_code, 200,
                         "refreshing the redirect target must remain a safe GET")

    def test_place_create_and_edit_finish_on_refresh_safe_named_get(self):
        create = self.client.post(reverse("editor:place-create"), self.place_payload())
        place = Location.objects.get(name="TEST — Navigation place")
        detail_url = reverse("editor:place-detail", args=(place.pk,))
        self.assert_stable_get_redirect(create, detail_url)

        edit = self.client.post(detail_url, self.place_payload(name="TEST — Navigation updated"))
        self.assert_stable_get_redirect(edit, detail_url)
        self.assertContains(self.client.get(detail_url), f'action="{detail_url}"')

    def test_entrance_create_and_edit_finish_on_refresh_safe_named_get(self):
        place = Location.objects.create(name="TEST — Parent", place_type=Location.PlaceType.BUILDING)
        create_url = reverse("editor:entrance-create", args=(place.pk,))
        create = self.client.post(create_url, self.entrance_payload())
        entrance = Entrance.objects.get(location=place)
        place_url = reverse("editor:place-detail", args=(place.pk,))
        self.assert_stable_get_redirect(create, place_url)

        edit_url = reverse("editor:entrance-edit", args=(place.pk, entrance.pk))
        edit = self.client.post(edit_url, self.entrance_payload(name="Updated entrance"))
        self.assert_stable_get_redirect(edit, place_url)
        self.assertContains(self.client.get(edit_url), f'action="{edit_url}"')

    def test_invalid_forms_stay_bound_without_mutation_and_keep_canonical_actions(self):
        create_url = reverse("editor:place-create")
        invalid_place = self.client.post(create_url, self.place_payload(name=""))
        self.assertEqual(invalid_place.status_code, 200)
        self.assertContains(invalid_place, f'action="{create_url}"')
        self.assertTrue(invalid_place.context["form"].errors)
        self.assertFalse(Location.objects.filter(description="Editor navigation regression record.").exists())

        place = Location.objects.create(name="TEST — Invalid entrance parent",
                                        place_type=Location.PlaceType.BUILDING)
        entrance_url = reverse("editor:entrance-create", args=(place.pk,))
        invalid_entrance = self.client.post(entrance_url, self.entrance_payload(latitude=""))
        self.assertEqual(invalid_entrance.status_code, 200)
        self.assertContains(invalid_entrance, f'action="{entrance_url}"')
        unsaved_entrance = invalid_entrance.context["entrance"]
        self.assertIsNotNone(unsaved_entrance.pk,
                             "UUID defaults exist before the model is persisted")
        self.assertFalse(Entrance.objects.filter(pk=unsaved_entrance.pk).exists())
        nonexistent_edit = reverse("editor:entrance-edit", args=(place.pk, unsaved_entrance.pk))
        phantom_actions = (
            nonexistent_edit,
            reverse("editor:entrance-verification", args=(place.pk, unsaved_entrance.pk)),
            reverse("editor:entrance-connection-candidates", args=(place.pk, unsaved_entrance.pk)),
            reverse("editor:entrance-connection-update", args=(place.pk, unsaved_entrance.pk)),
        )
        for phantom_action in phantom_actions:
            with self.subTest(phantom_action=phantom_action):
                self.assertNotContains(invalid_entrance, phantom_action)
        self.assertContains(invalid_entrance, "Add entrance")
        self.assertNotContains(invalid_entrance, "Find nearby connection")
        self.assertNotContains(invalid_entrance, "Mark entrance as field verified")
        self.assertTrue(invalid_entrance.context["form"].errors)
        self.assertFalse(place.entrances.exists())

    def test_verification_and_routing_actions_redirect_to_stable_gets(self):
        place = Location.objects.create(
            name="TEST — Actions", place_type=Location.PlaceType.BUILDING,
            representative_latitude=Decimal("6.518000"),
            representative_longitude=Decimal("3.374000"),
        )
        entrance = Entrance.objects.create(
            location=place, name="Main", entrance_type=Entrance.Type.MAIN,
            latitude=Decimal("6.518000"), longitude=Decimal("3.374000"),
            is_primary=True, is_active=True,
        )
        place_url = reverse("editor:place-detail", args=(place.pk,))
        entrance_url = reverse("editor:entrance-edit", args=(place.pk, entrance.pk))

        response = self.client.post(reverse("editor:place-verification", args=(place.pk,)), {
            "action": "grant", "reason": "Checked in the field.",
        })
        self.assert_stable_get_redirect(response, place_url)
        response = self.client.post(reverse("editor:entrance-verification", args=(place.pk, entrance.pk)), {
            "action": "grant", "reason": "Arrival point checked.",
        })
        self.assert_stable_get_redirect(response, entrance_url)

        node = WalkableNode.objects.create(
            label="Nearby junction", latitude=Decimal("6.518100"), longitude=Decimal("3.374000"),
            source_type=SourceType.MANUAL, verification_state=VerificationState.UNVERIFIED,
        )
        connector = {"type": "LineString", "coordinates": [
            [float(node.longitude), float(node.latitude)],
            [float(entrance.longitude), float(entrance.latitude)],
        ]}
        response = self.client.post(reverse(
            "editor:entrance-connection-update", args=(place.pk, entrance.pk),
        ), {"action": "connect", "node_id": node.pk,
            "connector_geometry": json.dumps(connector)})
        self.assert_stable_get_redirect(response, entrance_url)

    def test_cross_parent_entrance_remains_not_found(self):
        first = Location.objects.create(name="TEST — First", place_type=Location.PlaceType.BUILDING)
        second = Location.objects.create(name="TEST — Second", place_type=Location.PlaceType.BUILDING)
        entrance = Entrance.objects.create(
            location=second, name="Second entrance",
            latitude=Decimal("6.518000"), longitude=Decimal("3.374000"),
        )
        response = self.client.get(reverse("editor:entrance-edit", args=(first.pk, entrance.pk)))
        self.assertEqual(response.status_code, 404)

    def test_uuid_backed_graph_create_forms_do_not_present_unsaved_objects_as_existing(self):
        node_response = self.client.get(reverse("editor:node-create"))
        self.assertContains(node_response, "Add node")
        self.assertNotContains(node_response, "Edit node")
        self.assertFalse(WalkableNode.objects.filter(pk=node_response.context["node"].pk).exists())

        segment_response = self.client.get(reverse("editor:segment-create"))
        self.assertContains(segment_response, "Add segment")
        self.assertNotContains(segment_response, "Edit segment")
        self.assertNotContains(segment_response, "Split this segment explicitly")

    def test_least_privilege_place_and_entrance_mutations_redirect_to_permitted_gets(self):
        add_place = get_user_model().objects.create_user("add-place-only", password="test-password-42")
        add_place.user_permissions.add(Permission.objects.get(codename="add_location"))
        self.client.force_login(add_place)
        response = self.client.post(reverse("editor:place-create"), self.place_payload(
            name="TEST — Add-only place",
        ))
        self.assert_stable_get_redirect(response, reverse("editor:place-create"))

        parent = Location.objects.create(name="TEST — Least privilege parent",
                                         place_type=Location.PlaceType.BUILDING)
        add_entrance = get_user_model().objects.create_user("add-entrance-only", password="test-password-42")
        add_entrance.user_permissions.add(Permission.objects.get(codename="add_entrance"))
        self.client.force_login(add_entrance)
        create_url = reverse("editor:entrance-create", args=(parent.pk,))
        response = self.client.post(create_url, self.entrance_payload(name="Add-only entrance"))
        self.assert_stable_get_redirect(response, create_url)

        entrance = Entrance.objects.get(location=parent)
        change_entrance = get_user_model().objects.create_user("change-entrance-only", password="test-password-42")
        change_entrance.user_permissions.add(Permission.objects.get(codename="change_entrance"))
        self.client.force_login(change_entrance)
        edit_url = reverse("editor:entrance-edit", args=(parent.pk, entrance.pk))
        response = self.client.post(edit_url, self.entrance_payload(name="Changed safely"))
        self.assert_stable_get_redirect(response, edit_url)

    def test_least_privilege_graph_mutations_redirect_to_their_own_permitted_forms(self):
        add_node = get_user_model().objects.create_user("add-node-only", password="test-password-42")
        add_node.user_permissions.add(Permission.objects.get(codename="add_walkablenode"))
        self.client.force_login(add_node)
        create_url = reverse("editor:node-create")
        response = self.client.post(create_url, {
            "label": "Least privilege node", "latitude": "6.518000",
            "longitude": "3.374000", "is_active": "on",
        })
        self.assert_stable_get_redirect(response, create_url)

        node = WalkableNode.objects.get(label="Least privilege node")
        change_node = get_user_model().objects.create_user("change-node-only", password="test-password-42")
        change_node.user_permissions.add(Permission.objects.get(codename="change_walkablenode"))
        self.client.force_login(change_node)
        edit_url = reverse("editor:node-edit", args=(node.pk,))
        response = self.client.post(edit_url, {
            "label": "Least privilege node updated", "latitude": "6.518000",
            "longitude": "3.374000", "is_active": "on",
        })
        self.assert_stable_get_redirect(response, edit_url)


class EditorCsrfRecoveryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_superuser(
            "csrf-owner", "csrf@example.test", "Strong-test-password-42",
        )
        cls.place = Location.objects.create(name="TEST — CSRF place",
                                            place_type=Location.PlaceType.BUILDING)
        cls.entrance = Entrance.objects.create(
            location=cls.place, name="Main",
            latitude=Decimal("6.518000"), longitude=Decimal("3.374000"),
        )

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.owner)

    def assert_secure_recovery(self, action_url, expected_get):
        response = self.client.post(action_url, {})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.context["recovery_url"], expected_get)
        self.assertContains(response, f'href="{expected_get}"', status_code=403)
        self.assertEqual(self.client.get(expected_get).status_code, 200)

    def login_with_permission(self, username, codename):
        user = get_user_model().objects.create_user(username, password="test-password-42")
        user.user_permissions.add(Permission.objects.get(codename=codename))
        self.client.force_login(user)
        return user

    def test_post_only_actions_recover_to_canonical_get_pages(self):
        place_get = reverse("editor:place-detail", args=(self.place.pk,))
        entrance_get = reverse("editor:entrance-edit", args=(self.place.pk, self.entrance.pk))
        cases = (
            (reverse("editor:place-verification", args=(self.place.pk,)), place_get),
            (reverse("editor:entrance-verification", args=(self.place.pk, self.entrance.pk)), entrance_get),
            (reverse("editor:entrance-connection-update", args=(self.place.pk, self.entrance.pk)), entrance_get),
        )
        for action_url, expected_get in cases:
            with self.subTest(action_url=action_url):
                self.assert_secure_recovery(action_url, expected_get)

    def test_stale_nested_action_recovers_without_linking_to_missing_object(self):
        stale = reverse("editor:entrance-verification", args=(self.place.pk, self.entrance.pk))
        self.entrance.delete()
        response = self.client.post(stale, {})
        place_get = reverse("editor:place-detail", args=(self.place.pk,))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.context["recovery_url"], place_get)
        self.assertEqual(self.client.get(place_get).status_code, 200)

    def test_public_csrf_failure_recovers_to_the_public_map(self):
        public_client = Client(enforce_csrf_checks=True)
        response = public_client.post(
            reverse("contributions:submit"),
            data="{}",
            content_type="application/json",
        )
        map_url = reverse("locations:map")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.context["recovery_url"], map_url)
        self.assertContains(response, f'href="{map_url}"', status_code=403)

    def test_add_only_editors_recover_to_their_permitted_create_forms(self):
        cases = (
            ("csrf-add-entrance", "add_entrance",
             reverse("editor:entrance-create", args=(self.place.pk,))),
            ("csrf-add-floor", "add_floor",
             reverse("editor:floor-create", args=(self.place.pk,))),
            ("csrf-add-internal", "add_internalplace",
             reverse("editor:internal-create", args=(self.place.pk,))),
            ("csrf-add-node", "add_walkablenode", reverse("editor:node-create")),
            ("csrf-add-segment", "add_walkablesegment", reverse("editor:segment-create")),
        )
        for username, codename, form_url in cases:
            with self.subTest(codename=codename):
                self.login_with_permission(username, codename)
                self.assert_secure_recovery(form_url, form_url)

    def test_change_only_editors_recover_to_their_permitted_edit_forms(self):
        floor = Floor.objects.create(location=self.place, level=0, label="Ground floor")
        internal = InternalPlace.objects.create(
            location=self.place,
            floor=floor,
            name="TEST room",
            internal_type=InternalPlace.Type.OTHER,
        )
        first = WalkableNode.objects.create(
            label="First", latitude=Decimal("6.518000"), longitude=Decimal("3.374000"),
            source_type=SourceType.MANUAL, verification_state=VerificationState.UNVERIFIED,
        )
        second = WalkableNode.objects.create(
            label="Second", latitude=Decimal("6.518100"), longitude=Decimal("3.374000"),
            source_type=SourceType.MANUAL, verification_state=VerificationState.UNVERIFIED,
        )
        segment = WalkableSegment.objects.create(
            label="TEST segment",
            start_node=first,
            end_node=second,
            geometry={"type": "LineString", "coordinates": [
                [float(first.longitude), float(first.latitude)],
                [float(second.longitude), float(second.latitude)],
            ]},
            source_type=SourceType.MANUAL,
            verification_state=VerificationState.UNVERIFIED,
        )
        cases = (
            ("csrf-change-floor", "change_floor",
             reverse("editor:floor-edit", args=(self.place.pk, floor.pk))),
            ("csrf-change-internal", "change_internalplace",
             reverse("editor:internal-edit", args=(self.place.pk, internal.pk))),
            ("csrf-change-node", "change_walkablenode",
             reverse("editor:node-edit", args=(first.pk,))),
            ("csrf-change-segment", "change_walkablesegment",
             reverse("editor:segment-split", args=(segment.pk,)),
             reverse("editor:segment-edit", args=(segment.pk,))),
        )
        for case in cases:
            username, codename, action_url, *expected = case
            expected_get = expected[0] if expected else action_url
            with self.subTest(codename=codename):
                self.login_with_permission(username, codename)
                self.assert_secure_recovery(action_url, expected_get)

    def test_contribution_and_survey_specialists_recover_to_allowed_gets(self):
        contribution = Contribution.objects.create(
            request_id=uuid.uuid4(),
            status=Contribution.Status.APPROVED,
            contribution_type=Contribution.Type.OTHER,
            description="TEST approved report",
        )
        self.login_with_permission("csrf-resolution", "resolve_contribution")
        contribution_url = reverse("editor:contribution-detail", args=(contribution.pk,))
        self.assert_secure_recovery(contribution_url, contribution_url)

        owner = self.login_with_permission("csrf-surveyor", "conduct_path_survey")
        survey = PathSurvey.objects.create(owner=owner)
        detail_url = reverse("editor:survey-detail", args=(survey.pk,))
        self.assert_secure_recovery(
            reverse("editor:survey-samples", args=(survey.pk,)),
            detail_url,
        )

        self.login_with_permission("csrf-reviewer", "review_path_survey")
        self.assert_secure_recovery(
            reverse("editor:survey-match-review", args=(survey.pk, uuid.uuid4())),
            detail_url,
        )
