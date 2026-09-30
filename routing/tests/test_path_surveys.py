from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from routing.editor_services import save_segment, split_segment
from routing.editor_forms import WalkableNodeForm
from routing.models import (PathSurvey, PathSurveySample, SegmentVerificationRecord,
                            SurveySegmentMatch, VerificationState, WalkableNode, WalkableSegment)
from routing.survey_services import (_coverage, _longest_nearby_run,
                                     decide_verification, store_samples,
                                     transition_survey)


class PathSurveyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.editor = get_user_model().objects.create_user("surveyor", password="test-password-42")
        cls.editor.groups.add(Group.objects.get(name="Editor"))
        cls.reviewer = get_user_model().objects.create_user("reviewer", password="test-password-42")
        cls.reviewer.user_permissions.add(*Permission.objects.filter(codename__in=(
            "conduct_path_survey", "review_path_survey", "grant_field_verified", "revoke_field_verified")))

    def setUp(self):
        self.a = WalkableNode.objects.create(label="A", longitude=3.374000, latitude=6.518000,
                                              verification_state=VerificationState.UNVERIFIED)
        self.b = WalkableNode.objects.create(label="B", longitude=3.375000, latitude=6.518000,
                                              verification_state=VerificationState.UNVERIFIED)
        self.segment = WalkableSegment(start_node=self.a, end_node=self.b,
            geometry={"type":"LineString", "coordinates":[[3.374,6.518],[3.375,6.518]]},
            verification_state=VerificationState.UNVERIFIED)
        self.segment.full_clean(); self.segment.save()

    def test_explicit_lifecycle_and_interrupted_state(self):
        survey = PathSurvey.objects.create(owner=self.editor)
        self.assertFalse(survey.interrupted)
        transition_survey(survey, PathSurvey.Status.ACTIVE, self.editor)
        survey.refresh_from_db(); self.assertTrue(survey.interrupted)
        transition_survey(survey, PathSurvey.Status.PAUSED, self.editor)
        with self.assertRaises(ValidationError): transition_survey(survey, PathSurvey.Status.REVIEWED, self.editor)

    def test_duplicate_completion_is_idempotent_and_analysis_runs_once(self):
        survey = PathSurvey.objects.create(owner=self.editor, status=PathSurvey.Status.ACTIVE)
        with patch("routing.survey_services.analyse_survey") as analyse:
            transition_survey(survey, PathSurvey.Status.COMPLETED, self.editor)
            transition_survey(survey, PathSurvey.Status.COMPLETED, self.editor)
        survey.refresh_from_db()
        self.assertEqual(survey.status, PathSurvey.Status.COMPLETED)
        analyse.assert_called_once()

    def test_replayed_finish_post_is_safe_and_does_not_duplicate_matches(self):
        survey = PathSurvey.objects.create(owner=self.editor, status=PathSurvey.Status.ACTIVE)
        self.client.force_login(self.editor)
        url = reverse("editor:survey-detail", args=(survey.id,))
        first = self.client.post(url, {"action": "finish", "active_capture_seconds": "4"}, follow=True)
        second = self.client.post(url, {"action": "finish", "active_capture_seconds": "4"}, follow=True)
        self.assertEqual((first.status_code, second.status_code), (200, 200))
        self.assertNotContains(second, "Cannot change survey")
        self.assertEqual(survey.segment_matches.count(), 0)

    def test_only_owner_controls_active_survey(self):
        survey = PathSurvey.objects.create(owner=self.editor)
        with self.assertRaises(PermissionDenied): transition_survey(survey, PathSurvey.Status.ACTIVE, self.reviewer)

    def test_quality_jump_stationary_and_idempotent_batch(self):
        survey = PathSurvey.objects.create(owner=self.editor, status=PathSurvey.Status.ACTIVE)
        now = timezone.now()
        samples = store_samples(survey, [
            {"sequence":1,"captured_at":now,"longitude":3.374,"latitude":6.518,"accuracy":8},
            {"sequence":2,"captured_at":now+timedelta(seconds=5),"longitude":3.374,"latitude":6.518,"accuracy":8},
            {"sequence":3,"captured_at":now+timedelta(seconds=10),"longitude":3.38,"latitude":6.52,"accuracy":8},
            {"sequence":4,"captured_at":now+timedelta(seconds=15),"longitude":3.3741,"latitude":6.518,"accuracy":70},
        ], self.editor)
        self.assertEqual([x.classification for x in samples], ["ACCEPTED","REJECTED","REJECTED","REJECTED"])
        self.assertEqual(len(store_samples(survey, [{"sequence":1,"captured_at":now,"longitude":3.374,
            "latitude":6.518,"accuracy":8}], self.editor)), 1)
        self.assertEqual(survey.samples.count(), 4)

    def test_idempotent_replay_requires_all_raw_evidence_to_match(self):
        survey = PathSurvey.objects.create(owner=self.editor, status=PathSurvey.Status.ACTIVE)
        now = timezone.now()
        payload = {"sequence": 1, "captured_at": now, "longitude": 3.374, "latitude": 6.518,
                   "accuracy": 8, "speed": 1.2, "heading": 85}
        store_samples(survey, [payload], self.editor)
        self.assertEqual(store_samples(survey, [payload], self.editor)[0].sequence, 1)
        with self.assertRaisesMessage(ValidationError, "different raw evidence"):
            store_samples(survey, [{**payload, "accuracy": 18}], self.editor)
        self.assertEqual(survey.samples.count(), 1)

    def test_out_of_order_batch_is_classified_in_sequence_order(self):
        survey = PathSurvey.objects.create(owner=self.editor, status=PathSurvey.Status.ACTIVE)
        now = timezone.now()
        stored = store_samples(survey, [
            {"sequence": 2, "captured_at": now + timedelta(seconds=2), "longitude": 3.37404,
             "latitude": 6.518, "accuracy": 5},
            {"sequence": 1, "captured_at": now, "longitude": 3.374, "latitude": 6.518, "accuracy": 5},
        ], self.editor)
        self.assertEqual([sample.sequence for sample in stored], [1, 2])
        self.assertEqual([sample.classification for sample in stored], ["ACCEPTED", "ACCEPTED"])

    def test_paused_survey_accepts_pending_buffer_and_completed_survey_only_accepts_exact_replay(self):
        survey = PathSurvey.objects.create(owner=self.editor, status=PathSurvey.Status.PAUSED)
        now = timezone.now()
        payload = {"sequence": 1, "captured_at": now, "longitude": 3.374,
                   "latitude": 6.518, "accuracy": 8}
        store_samples(survey, [payload], self.editor)
        survey.status = PathSurvey.Status.COMPLETED
        survey.save(update_fields=("status",))
        self.assertEqual(store_samples(survey, [payload], self.editor)[0].sequence, 1)
        with self.assertRaisesMessage(ValidationError, "active or paused"):
            store_samples(survey, [{**payload, "sequence": 2}], self.editor)

    def test_accuracy_and_time_aware_downsampling_uses_last_usable_reference(self):
        survey = PathSurvey.objects.create(owner=self.editor, status=PathSurvey.Status.ACTIVE)
        now = timezone.now()
        samples = store_samples(survey, [
            {"sequence":1,"captured_at":now,"longitude":3.374,"latitude":6.518,"accuracy":5},
            {"sequence":2,"captured_at":now+timedelta(seconds=1),"longitude":3.374005,"latitude":6.518,"accuracy":5},
            {"sequence":3,"captured_at":now+timedelta(seconds=2),"longitude":3.374010,"latitude":6.518,"accuracy":5},
            {"sequence":4,"captured_at":now+timedelta(seconds=4),"longitude":3.374020,"latitude":6.518,"accuracy":5},
            {"sequence":5,"captured_at":now+timedelta(seconds=5),"longitude":3.374025,"latitude":6.518,"accuracy":5},
            {"sequence":6,"captured_at":now+timedelta(seconds=10),"longitude":3.374020,"latitude":6.518,"accuracy":5},
        ], self.editor)
        self.assertEqual([sample.classification for sample in samples],
                         ["ACCEPTED", "REJECTED", "REJECTED", "ACCEPTED", "REJECTED", "ACCEPTED"])
        self.assertEqual(samples[1].rejection_reason, "Redundant high-frequency sample.")

    def test_stationary_high_frequency_is_suppressed_but_periodic_evidence_remains(self):
        survey = PathSurvey.objects.create(owner=self.editor, status=PathSurvey.Status.ACTIVE)
        now = timezone.now()
        samples = store_samples(survey, [
            {"sequence":1,"captured_at":now,"longitude":3.374,"latitude":6.518,"accuracy":8},
            {"sequence":2,"captured_at":now+timedelta(seconds=1),"longitude":3.374001,"latitude":6.518,"accuracy":8},
            {"sequence":3,"captured_at":now+timedelta(seconds=4),"longitude":3.374001,"latitude":6.518,"accuracy":8},
            {"sequence":4,"captured_at":now+timedelta(seconds=6),"longitude":3.374001,"latitude":6.518,"accuracy":8},
        ], self.editor)
        self.assertEqual([sample.classification for sample in samples],
                         ["ACCEPTED", "REJECTED", "REJECTED", "ACCEPTED"])

    def test_normal_walking_updates_are_not_lost_to_high_frequency_downsampling(self):
        survey = PathSurvey.objects.create(owner=self.editor, status=PathSurvey.Status.ACTIVE)
        now = timezone.now()
        samples = store_samples(survey, [
            {"sequence":index+1,"captured_at":now+timedelta(seconds=index),
             "longitude":3.374 + index*.00002,"latitude":6.518,"accuracy":5}
            for index in range(5)
        ], self.editor)
        self.assertEqual([sample.classification for sample in samples], ["ACCEPTED"] * 5)

    def test_candidate_coverage_uses_only_contiguous_supported_points(self):
        full = _coverage(self.segment, [[3.374,6.518],[3.3745,6.518],[3.375,6.518]])
        partial = _coverage(self.segment, [[3.374,6.518],[3.3745,6.518]])
        sparse = _coverage(self.segment, [[3.37448,6.518],[3.37452,6.518]])
        self.assertGreater(full, 99)
        self.assertGreater(partial, 45); self.assertLess(partial, 55)
        self.assertLess(sparse, 6)
        trace = [[3.374,6.518],[3.3745,6.518],[3.38,6.52],[3.375,6.518]]
        projections = [SimpleNamespace(distance_metres=value) for value in (2, 2, 40, 2)]
        run = _longest_nearby_run(trace, projections)
        self.assertEqual([point for point, _ in run], trace[:2])

    def test_zero_coverage_candidate_is_diagnostic_but_discrepancy_stays_primary(self):
        survey = PathSurvey.objects.create(owner=self.editor, status=PathSurvey.Status.COMPLETED)
        ambiguous = SurveySegmentMatch.objects.create(survey=survey, segment=self.segment,
            segment_revision=1, segment_fingerprint=self.segment.geometry_fingerprint,
            classification=SurveySegmentMatch.Classification.AMBIGUOUS,
            coverage_percent=0, mean_distance_metres=3)
        c = WalkableNode.objects.create(label="C", longitude=3.374000, latitude=6.518100,
                                         verification_state=VerificationState.UNVERIFIED)
        d = WalkableNode.objects.create(label="D", longitude=3.375000, latitude=6.518100,
                                         verification_state=VerificationState.UNVERIFIED)
        other = WalkableSegment.objects.create(start_node=c, end_node=d,
            geometry={"type":"LineString","coordinates":[[3.374,6.5181],[3.375,6.5181]]},
            verification_state=VerificationState.UNVERIFIED)
        discrepancy = SurveySegmentMatch.objects.create(survey=survey, segment=other,
            segment_revision=1, segment_fingerprint=other.geometry_fingerprint,
            classification=SurveySegmentMatch.Classification.DISCREPANCY,
            coverage_percent=0, mean_distance_metres=15)
        self.client.force_login(self.editor)
        response = self.client.get(reverse("editor:survey-detail", args=(survey.id,)))
        self.assertIn(discrepancy, response.context["matches"])
        self.assertIn(ambiguous, response.context["diagnostic_matches"])
        self.assertContains(response, "retained for diagnostics")

    def test_completed_review_page_is_read_only_and_summarises_match_state(self):
        survey = PathSurvey.objects.create(owner=self.editor, status=PathSurvey.Status.ACTIVE)
        PathSurveySample.objects.create(survey=survey, sequence=1, captured_at=timezone.now(),
            longitude=3.374, latitude=6.518, accuracy_metres=8,
            classification=PathSurveySample.Classification.ACCEPTED)
        survey.status = PathSurvey.Status.COMPLETED
        survey.save(update_fields=("status",))
        match = SurveySegmentMatch.objects.create(survey=survey, segment=self.segment,
            segment_revision=1, segment_fingerprint=self.segment.geometry_fingerprint,
            classification=SurveySegmentMatch.Classification.DISCREPANCY,
            coverage_percent=20, mean_distance_metres=14)
        node_count, segment_count = WalkableNode.objects.count(), WalkableSegment.objects.count()
        self.client.force_login(self.editor)
        response = self.client.get(reverse("editor:survey-detail", args=(survey.id,)))
        self.assertContains(response, 'id="survey-review-map"', html=False)
        self.assertContains(response, "Pending review")
        self.assertEqual(response.context["match_summary"]["pending"], 1)
        self.assertEqual(response.context["match_summary"]["reviewed"], 0)
        self.assertEqual(WalkableNode.objects.count(), node_count)
        self.assertEqual(WalkableSegment.objects.count(), segment_count)
        match.refresh_from_db()
        self.assertEqual(match.disposition, SurveySegmentMatch.Disposition.PENDING)

    def test_record_review_only_persists_reason_and_has_visible_feedback(self):
        survey = PathSurvey.objects.create(owner=self.editor, status=PathSurvey.Status.COMPLETED)
        match = SurveySegmentMatch.objects.create(survey=survey, segment=self.segment,
            segment_revision=1, segment_fingerprint=self.segment.geometry_fingerprint,
            classification=SurveySegmentMatch.Classification.DISCREPANCY,
            coverage_percent=20, mean_distance_metres=14)
        self.client.force_login(self.reviewer)
        response = self.client.post(reverse("editor:survey-match-review", args=(survey.id, match.id)), {
            "action": "review", "disposition": "USEFUL_PARTIAL",
            "reason": "Useful evidence; another pass is still required.",
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        match.refresh_from_db()
        self.assertEqual(match.disposition, SurveySegmentMatch.Disposition.USEFUL_PARTIAL)
        self.assertEqual(match.reviewer_note, "Useful evidence; another pass is still required.")
        self.assertContains(response, "Review recorded")
        self.assertContains(response, "Useful evidence; another pass is still required.")
        self.assertEqual(response.context["match_summary"]["reviewed"], 1)

    def test_record_review_only_requires_reason_and_known_disposition(self):
        survey = PathSurvey.objects.create(owner=self.editor, status=PathSurvey.Status.COMPLETED)
        match = SurveySegmentMatch.objects.create(survey=survey, segment=self.segment,
            segment_revision=1, segment_fingerprint=self.segment.geometry_fingerprint,
            classification=SurveySegmentMatch.Classification.DISCREPANCY,
            coverage_percent=20, mean_distance_metres=14)
        self.client.force_login(self.reviewer)
        url = reverse("editor:survey-match-review", args=(survey.id, match.id))
        self.client.post(url, {"action": "review", "disposition": "USEFUL_PARTIAL", "reason": ""})
        match.refresh_from_db(); self.assertEqual(match.disposition, SurveySegmentMatch.Disposition.PENDING)
        self.client.post(url, {"action": "review", "disposition": "NOT_REAL", "reason": "Checked"})
        match.refresh_from_db(); self.assertEqual(match.disposition, SurveySegmentMatch.Disposition.PENDING)

    def test_completed_evidence_is_immutable_and_matching_creates_revision_bound_candidate(self):
        survey = PathSurvey.objects.create(owner=self.editor, status=PathSurvey.Status.ACTIVE)
        now = timezone.now()
        store_samples(survey, [{"sequence":i+1,"captured_at":now+timedelta(seconds=i*10),
            "longitude":3.374+i*.0002,"latitude":6.518,"accuracy":8} for i in range(6)], self.editor)
        transition_survey(survey, PathSurvey.Status.COMPLETED, self.editor)
        survey.refresh_from_db(); match = survey.segment_matches.get(segment=self.segment)
        self.assertEqual(match.segment_revision, self.segment.geometry_revision)
        sample = survey.samples.first(); sample.accuracy_metres = 9
        with self.assertRaises(ValidationError): sample.save()

    def test_no_candidate_is_represented_without_fake_match(self):
        survey = PathSurvey.objects.create(owner=self.editor, status=PathSurvey.Status.ACTIVE)
        now = timezone.now()
        store_samples(survey, [{"sequence":1,"captured_at":now,"longitude":3.39,"latitude":6.53,"accuracy":8},
            {"sequence":2,"captured_at":now+timedelta(seconds=10),"longitude":3.3901,"latitude":6.53,"accuracy":8}], self.editor)
        transition_survey(survey, PathSurvey.Status.COMPLETED, self.editor)
        self.assertFalse(survey.segment_matches.exists())

    def test_verification_requires_permission_current_revision_and_low_coverage_override(self):
        survey = PathSurvey.objects.create(owner=self.editor, status=PathSurvey.Status.COMPLETED)
        match = SurveySegmentMatch.objects.create(survey=survey, segment=self.segment,
            segment_revision=1, segment_fingerprint=self.segment.geometry_fingerprint,
            classification=SurveySegmentMatch.Classification.PARTIAL, coverage_percent=60, mean_distance_metres=2)
        with self.assertRaises(PermissionDenied): decide_verification(match, grant=True, actor=self.editor, reason="override")
        with self.assertRaises(ValidationError): decide_verification(match, grant=True, actor=self.reviewer, reason="Looks sound")
        decide_verification(match, grant=True, actor=self.reviewer, reason="Explicit override: field evidence is sufficient")
        self.segment.refresh_from_db(); self.assertEqual(self.segment.verification_state, VerificationState.FIELD_VERIFIED)
        self.assertEqual(SegmentVerificationRecord.objects.get().action, SegmentVerificationRecord.Action.GRANTED)

    def test_material_mutation_increments_revision_demotes_and_preserves_history(self):
        self.segment.verification_state = VerificationState.FIELD_VERIFIED; self.segment.save()
        cleaned = {"label":"changed", "start_node":self.a, "end_node":self.b,
            "geometry":{"type":"LineString","coordinates":[[3.374,6.518],[3.3745,6.5181],[3.375,6.518]]},
            "is_bidirectional":True, "is_active":True}
        for key, value in cleaned.items(): setattr(self.segment, key, value)
        save_segment(segment=self.segment, cleaned_data=cleaned, actor=self.editor)
        self.segment.refresh_from_db(); self.assertEqual(self.segment.geometry_revision, 2)
        self.assertEqual(self.segment.verification_state, VerificationState.UNVERIFIED)
        self.assertTrue(self.segment.verification_records.filter(action="INVALIDATED").exists())

    def test_split_preserves_relational_lineage_and_verification_history(self):
        self.segment.verification_state = VerificationState.FIELD_VERIFIED; self.segment.save()
        _, left, right = split_segment(self.segment, (3.3745,6.518), self.editor)
        self.assertEqual((left.derived_from_segment_id, right.derived_from_segment_id), (self.segment.id,self.segment.id))
        self.assertEqual(left.verification_state, VerificationState.UNVERIFIED)

    def test_connected_node_cannot_be_deactivated_before_its_graph_references(self):
        self.a.refresh_from_db()
        form = WalkableNodeForm({"label": self.a.label, "latitude": str(self.a.latitude),
            "longitude": str(self.a.longitude)}, instance=self.a, locked=True)
        self.assertFalse(form.is_valid())
        self.assertIn("Deactivate connected segments and anchors first", str(form.non_field_errors()))

    def test_private_routes_enforce_authentication_and_ownership(self):
        survey = PathSurvey.objects.create(owner=self.editor)
        self.assertEqual(self.client.get(reverse("editor:survey-detail", args=(survey.id,))).status_code, 302)
        outsider = get_user_model().objects.create_user("outsider", password="x")
        outsider.user_permissions.add(Permission.objects.get(codename="conduct_path_survey"))
        self.client.force_login(outsider)
        self.assertEqual(self.client.get(reverse("editor:survey-detail", args=(survey.id,))).status_code, 403)

    def test_editor_survey_ui_never_exposes_evidence_publicly(self):
        survey = PathSurvey.objects.create(owner=self.editor)
        self.client.force_login(self.editor)
        response = self.client.get(reverse("editor:survey-detail", args=(survey.id,)))
        self.assertContains(response, "never rewrite paths or verify them automatically", status_code=200)
        self.assertNotIn(str(survey.id), self.client.get("/api/locations/").content.decode())

    def test_completed_summary_uses_persisted_classifications(self):
        survey = PathSurvey.objects.create(owner=self.editor, status=PathSurvey.Status.ACTIVE,
                                            started_at=timezone.now()-timedelta(seconds=254))
        now=timezone.now()
        store_samples(survey,[
            {"sequence":1,"captured_at":now,"longitude":3.374,"latitude":6.518,"accuracy":8},
            {"sequence":2,"captured_at":now+timedelta(seconds=10),"longitude":3.3741,"latitude":6.518,"accuracy":40},
            {"sequence":3,"captured_at":now+timedelta(seconds=20),"longitude":3.3742,"latitude":6.518,"accuracy":500},
        ],self.editor)
        transition_survey(survey,PathSurvey.Status.COMPLETED,self.editor)
        self.client.force_login(self.editor)
        response=self.client.get(reverse("editor:survey-detail",args=(survey.id,)))
        self.assertContains(response,'id="survey-raw">3</strong>',html=False)
        self.assertContains(response,'id="survey-usable">2</strong>',html=False)
        self.assertContains(response,'id="survey-rejected">1</strong>',html=False)
        self.assertContains(response,"3 raw")
        self.assertContains(response,"2 usable")
        self.assertContains(response,"1 rejected")

    def test_active_timing_is_monotonic_persists_and_is_separate_from_session_duration(self):
        survey=PathSurvey.objects.create(owner=self.editor,status=PathSurvey.Status.ACTIVE,
            started_at=timezone.now()-timedelta(seconds=254))
        self.client.force_login(self.editor)
        url=reverse("editor:survey-timing",args=(survey.id,))
        self.assertEqual(self.client.post(url,data='{"active_capture_seconds": 12}',content_type="application/json").status_code,200)
        self.client.post(url,data='{"active_capture_seconds": 8}',content_type="application/json")
        survey.refresh_from_db(); self.assertEqual(survey.active_capture_seconds,12)
        self.assertTrue(survey.active_capture_tracking_started)
        pause=self.client.post(reverse("editor:survey-detail",args=(survey.id,)),
            {"action":"pause","active_capture_seconds":"15"})
        self.assertEqual(pause.status_code,302)
        survey.refresh_from_db(); self.assertEqual(survey.active_capture_seconds,15)
        self.assertEqual(survey.status,PathSurvey.Status.PAUSED)
        before=survey.active_capture_seconds
        self.client.get(reverse("editor:survey-detail",args=(survey.id,)))
        survey.refresh_from_db(); self.assertEqual(survey.active_capture_seconds,before)
        self.assertGreaterEqual(survey.session_duration_seconds,254)

    def test_active_and_paused_field_map_uses_only_persisted_usable_trace(self):
        survey=PathSurvey.objects.create(owner=self.editor,status=PathSurvey.Status.ACTIVE,started_at=timezone.now())
        now=timezone.now()
        store_samples(survey,[
            {"sequence":1,"captured_at":now,"longitude":3.374,"latitude":6.518,"accuracy":8},
            {"sequence":2,"captured_at":now+timedelta(seconds=10),"longitude":3.3742,"latitude":6.518,"accuracy":40},
            {"sequence":3,"captured_at":now+timedelta(seconds=20),"longitude":3.39,"latitude":6.53,"accuracy":500},
        ],self.editor)
        self.client.force_login(self.editor)
        response=self.client.get(reverse("editor:survey-detail",args=(survey.id,)))
        self.assertContains(response,'id="survey-field-map"',html=False)
        self.assertEqual(response.context["survey_trace"],[[3.374,6.518],[3.3742,6.518]])
        self.assertEqual(len(response.context["survey_network"]["features"]),1)
        synced=self.client.post(reverse("editor:survey-samples",args=(survey.id,)),data=(
            '{"samples":[{"sequence":3,"captured_at":"'+(now+timedelta(seconds=20)).isoformat()+
            '","longitude":3.39,"latitude":6.53,"accuracy":500}]}'),content_type="application/json")
        self.assertEqual(synced.json()["trace"],[[3.374,6.518],[3.3742,6.518]])
        transition_survey(survey,PathSurvey.Status.PAUSED,self.editor)
        paused=self.client.get(reverse("editor:survey-detail",args=(survey.id,)))
        self.assertContains(paused,'id="survey-field-map"',html=False)
        self.assertEqual(paused.context["survey_trace"],response.context["survey_trace"])


class RoutingAdminHardeningTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.administrator = get_user_model().objects.create_superuser(
            "routing-admin", "routing-admin@example.test", "Strong-test-password-42"
        )
        cls.node = WalkableNode.objects.create(
            label="Protected node", longitude=3.374, latitude=6.518,
            verification_state=VerificationState.UNVERIFIED,
        )

    def test_graph_and_evidence_admins_are_inspection_only(self):
        request = RequestFactory().get("/admin/")
        request.user = self.administrator
        protected_models = (
            WalkableNode, WalkableSegment, PathSurvey, PathSurveySample,
            SurveySegmentMatch, SegmentVerificationRecord,
        )
        for model in protected_models:
            model_admin = admin.site._registry[model]
            self.assertFalse(model_admin.has_add_permission(request), model.__name__)
            self.assertFalse(model_admin.has_delete_permission(request), model.__name__)
            self.assertEqual(
                set(model_admin.get_readonly_fields(request)),
                {field.name for field in model._meta.fields},
                model.__name__,
            )

    def test_admin_cannot_submit_connected_node_coordinates_or_delete_it(self):
        self.client.force_login(self.administrator)
        change_url = reverse("admin:routing_walkablenode_change", args=(self.node.pk,))
        response = self.client.get(change_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="longitude"')
        delete_url = reverse("admin:routing_walkablenode_delete", args=(self.node.pk,))
        self.assertEqual(self.client.get(delete_url).status_code, 403)
