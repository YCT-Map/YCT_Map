import json
import uuid

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from locations.models import Location
from contributions.models import Contribution


class ContributionSubmissionTests(TestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse("contributions:submit")
        self.location = Location.objects.create(
            name="DEMO — Library", category=Location.Category.LIBRARY,
            entrance_latitude="6.518500", entrance_longitude="3.374200",
            verification_state=Location.VerificationState.DEMO,
        )

    def payload(self, **overrides):
        data = {
            "request_id": str(uuid.uuid4()),
            "type": Contribution.Type.CORRECT_LOCATION,
            "target_location": str(self.location.id),
            "description": "The displayed point needs review.",
        }
        data.update(overrides)
        return data

    def post(self, payload, client=None):
        return (client or self.client).post(self.url, json.dumps(payload), content_type="application/json")

    def test_anonymous_submission_is_pending_and_does_not_change_location(self):
        self.location.refresh_from_db()
        before = (self.location.name, self.location.entrance_latitude, self.location.entrance_longitude)
        response = self.post(self.payload(description="<script>alert(1)</script> review this point"))
        self.assertEqual(response.status_code, 201)
        contribution = Contribution.objects.get()
        self.assertEqual(contribution.status, Contribution.Status.PENDING)
        self.assertIn("<script>", contribution.description)
        self.location.refresh_from_db()
        self.assertEqual(before, (self.location.name, self.location.entrance_latitude, self.location.entrance_longitude))

    def test_new_place_accepts_category_and_optional_point(self):
        response = self.post(self.payload(
            type=Contribution.Type.ADD_LOCATION, target_location=None,
            proposed_name="Proposed reading room", proposed_category=Location.Category.LIBRARY,
            proposed_point={"latitude": 6.5186, "longitude": 3.3743},
        ))
        self.assertEqual(response.status_code, 201)
        contribution = Contribution.objects.get()
        self.assertEqual(str(contribution.proposed_latitude), "6.518600")

    def test_invalid_type_target_coordinate_and_required_fields_are_rejected(self):
        cases = [
            (self.payload(type="UNKNOWN"), 400, "INVALID_TYPE"),
            (self.payload(target_location=str(uuid.uuid4())), 400, "INVALID_TARGET"),
            (self.payload(proposed_point={"latitude": 200, "longitude": 3}), 422, "INVALID_COORDINATE"),
            (self.payload(proposed_point={"latitude": 6.5}), 400, "INVALID_COORDINATE"),
            (self.payload(description=""), 422, "VALIDATION_ERROR"),
            (self.payload(type=Contribution.Type.ADD_LOCATION, target_location=None), 422, "VALIDATION_ERROR"),
        ]
        for payload, status, code in cases:
            with self.subTest(code=code):
                cache.clear()
                response = self.post(payload)
                self.assertEqual(response.status_code, status)
                self.assertEqual(response.json()["code"], code)

    def test_oversized_text_is_rejected(self):
        response = self.post(self.payload(description="x" * 1001))
        self.assertEqual(response.status_code, 422)

    def test_request_id_is_idempotent(self):
        payload = self.payload()
        self.assertEqual(self.post(payload).status_code, 201)
        replay = self.post(payload)
        self.assertEqual(replay.status_code, 200)
        self.assertTrue(replay.json()["duplicate_request"])
        self.assertEqual(Contribution.objects.count(), 1)

    def test_session_rate_limit_allows_three_then_returns_429(self):
        for _ in range(3):
            self.assertEqual(self.post(self.payload()).status_code, 201)
        response = self.post(self.payload())
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["code"], "RATE_LIMITED")

    def test_maplibre_precision_is_normalized_to_six_decimal_places(self):
        response = self.post(self.payload(proposed_point={
            "latitude": 6.518123456789,
            "longitude": 3.374987654321,
        }))
        self.assertEqual(response.status_code, 201)
        contribution = Contribution.objects.get()
        self.assertEqual(str(contribution.proposed_latitude), "6.518123")
        self.assertEqual(str(contribution.proposed_longitude), "3.374988")

    def test_validation_failures_do_not_consume_accepted_submission_quota(self):
        for _ in range(2):
            response = self.post(self.payload(description=""))
            self.assertEqual(response.status_code, 422)
        for _ in range(3):
            self.assertEqual(self.post(self.payload()).status_code, 201)
        self.assertEqual(self.post(self.payload()).status_code, 429)

    def test_idempotent_retry_does_not_consume_another_accepted_slot(self):
        payload = self.payload()
        self.assertEqual(self.post(payload).status_code, 201)
        self.assertEqual(self.post(payload).status_code, 200)
        self.assertEqual(self.post(self.payload()).status_code, 201)
        self.assertEqual(self.post(self.payload()).status_code, 201)
        self.assertEqual(self.post(self.payload()).status_code, 429)

    def test_repeated_invalid_traffic_is_bounded_by_abuse_limit(self):
        for _ in range(30):
            response = self.post(self.payload(type="INVALID"))
            self.assertEqual(response.status_code, 400)
        response = self.post(self.payload(type="INVALID"))
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["code"], "RATE_LIMITED")

    def test_csrf_is_required_and_get_is_not_allowed(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(self.post(self.payload(), client).status_code, 403)
        self.assertEqual(self.client.get(self.url).status_code, 405)


class ContributionModerationTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_superuser("moderator", "", "test")
        self.contribution = Contribution.objects.create(
            request_id=uuid.uuid4(), contribution_type=Contribution.Type.OTHER,
            description="Review this report.",
        )

    def test_admin_requires_staff(self):
        response = self.client.get(reverse("admin:contributions_contribution_changelist"))
        self.assertEqual(response.status_code, 302)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse("admin:contributions_contribution_changelist")).status_code, 200)

    def test_moderation_records_reviewer_and_timestamp(self):
        self.client.force_login(self.staff)
        change_url = reverse("admin:contributions_contribution_change", args=[self.contribution.pk])
        response = self.client.post(change_url, {
            "contribution_type": Contribution.Type.OTHER,
            "status": Contribution.Status.APPROVED,
            "description": self.contribution.description,
            "proposed_name": "", "proposed_category": "", "context": "",
            "moderator_note": "Accepted as input for later editor work.",
            "target_location": "", "merged_into": "", "resolved_location": "",
            "proposed_latitude": "", "proposed_longitude": "", "_save": "Save",
        })
        self.assertEqual(response.status_code, 302)
        self.contribution.refresh_from_db()
        self.assertEqual(self.contribution.reviewed_by, self.staff)
        self.assertIsNotNone(self.contribution.reviewed_at)

    def test_merged_status_requires_merge_target(self):
        self.contribution.status = Contribution.Status.MERGED
        with self.assertRaises(ValidationError):
            self.contribution.full_clean()
