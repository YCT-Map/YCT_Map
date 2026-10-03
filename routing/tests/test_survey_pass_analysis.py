from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from routing.candidate_services import create_candidate_path, preview_candidate_graph_change
from routing.models import (PathSurvey, PathSurveySample, SegmentVerificationRecord,
                            SurveySegmentMatch, VerificationState, WalkableNode, WalkableSegment)
from routing.survey_analysis import (EvidencePoint, analyse_existing_segment,
                                     analyse_cumulative_existing_segment,
                                     candidate_runs, detect_segment_passes,
                                     discover_candidate_paths,
                                     discover_cumulative_candidate_paths)
from routing.survey_services import analyse_survey, analyse_survey_dry_run


class PassAwareSurveyAnalysisTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.editor = get_user_model().objects.create_user("pass-editor", password="test-password-42")
        cls.editor.groups.add(Group.objects.get(name="Editor"))

    def setUp(self):
        self.a = WalkableNode.objects.create(longitude=3.374, latitude=6.518,
                                              verification_state=VerificationState.UNVERIFIED)
        self.b = WalkableNode.objects.create(longitude=3.375, latitude=6.518,
                                              verification_state=VerificationState.UNVERIFIED)
        self.segment = WalkableSegment.objects.create(
            start_node=self.a, end_node=self.b,
            geometry={"type": "LineString", "coordinates": [[3.374, 6.518], [3.375, 6.518]]},
            verification_state=VerificationState.UNVERIFIED,
        )
        self.now = timezone.now() + timedelta(seconds=1)

    def points(self, coordinates, *, start_seconds=0, step_seconds=5, accuracy=5):
        return [EvidencePoint(tuple(coordinate), self.now + timedelta(
            seconds=start_seconds + index * step_seconds), accuracy, index + 1)
            for index, coordinate in enumerate(coordinates)]

    def straight(self, reverse=False):
        values = [[3.374 + index * .0002, 6.518] for index in range(6)]
        return list(reversed(values)) if reverse else values

    def finalized_survey(self, coordinates, *, status=PathSurvey.Status.COMPLETED,
                         start_seconds=0, accuracy=5, rejected=False):
        survey = PathSurvey.objects.create(owner=self.editor, status=status)
        PathSurveySample.objects.bulk_create([
            PathSurveySample(
                survey=survey,
                sequence=index + 1,
                captured_at=self.now + timedelta(seconds=start_seconds + index * 5),
                longitude=coordinate[0],
                latitude=coordinate[1],
                accuracy_metres=accuracy,
                classification=(PathSurveySample.Classification.REJECTED
                                if rejected else PathSurveySample.Classification.ACCEPTED),
                rejection_reason="test rejection" if rejected else "",
            )
            for index, coordinate in enumerate(coordinates)
        ])
        return survey

    def test_clean_and_high_frequency_callbacks_remain_one_pass(self):
        clean = detect_segment_passes(self.points(self.straight()), self.segment)
        dense = detect_segment_passes(self.points(
            [[3.374 + index * .00005, 6.518] for index in range(21)], step_seconds=.5), self.segment)
        self.assertEqual((len(clean), len(dense)), (1, 1))
        self.assertTrue(clean[0].strong)

    def test_departure_return_are_independent_but_one_brief_dropout_is_not(self):
        first = self.points(self.straight())
        off = self.points([[3.376, 6.519], [3.3762, 6.519]], start_seconds=35)
        second = self.points(self.straight(reverse=True), start_seconds=50)
        passes = detect_segment_passes(first + off + second, self.segment)
        self.assertEqual(len(passes), 2)
        brief = first[:3] + self.points([[3.376, 6.519]], start_seconds=15) + first[3:]
        self.assertEqual(len(detect_segment_passes(brief, self.segment)), 1)

    def test_crossing_and_parallel_path_do_not_verify_the_wrong_segment(self):
        crossing = self.points([[3.3745, 6.5177], [3.3745, 6.5179], [3.3745, 6.518],
                                [3.3745, 6.5181], [3.3745, 6.5183]])
        self.assertFalse(analyse_existing_segment(crossing, self.segment)["auto_verify"])
        c = WalkableNode.objects.create(longitude=3.374, latitude=6.51804,
                                         verification_state=VerificationState.UNVERIFIED)
        d = WalkableNode.objects.create(longitude=3.375, latitude=6.51804,
                                         verification_state=VerificationState.UNVERIFIED)
        parallel = WalkableSegment.objects.create(start_node=c, end_node=d,
            geometry={"type": "LineString", "coordinates": [[3.374, 6.51804], [3.375, 6.51804]]},
            verification_state=VerificationState.UNVERIFIED)
        trace = self.points([[3.374 + index * .0002, 6.518] for index in range(6)])
        target = analyse_existing_segment(trace, self.segment, [self.segment, parallel])
        self.assertFalse(target["auto_verify"])
        self.assertTrue(target["best"].conflict)
        wrong = analyse_existing_segment(trace, parallel, [self.segment, parallel])
        self.assertFalse(wrong["auto_verify"])
        self.assertTrue(wrong["best"].conflict)
        self.assertEqual(wrong["classification"], "AMBIGUOUS")

    def test_low_coverage_offset_accuracy_and_random_nearby_points_do_not_verify(self):
        short = self.points([[3.374, 6.518], [3.3741, 6.518], [3.3742, 6.518],
                             [3.37425, 6.518], [3.3743, 6.518]])
        offset = self.points([[3.374 + index*.0002, 6.51808] for index in range(6)])
        poor = self.points(self.straight(), accuracy=18)
        random = self.points([[3.3741, 6.518], [3.3748, 6.518], [3.3742, 6.518],
                              [3.3749, 6.518], [3.3743, 6.518]])
        for trace in (short, offset, poor, random):
            self.assertFalse(analyse_existing_segment(trace, self.segment)["auto_verify"])

    def test_contiguous_partial_passes_can_supply_cumulative_coverage(self):
        first = self.points([[3.374 + index * .00015, 6.518] for index in range(5)])
        second = self.points([[3.3744 + index * .00015, 6.518] for index in range(5)],
                             start_seconds=60)
        result = analyse_cumulative_existing_segment([first, second], self.segment)
        self.assertEqual(len(result["supporting_passes"]), 2)
        self.assertGreaterEqual(result["cumulative_coverage_percent"], 80)
        self.assertTrue(result["auto_verify"])

    def test_conflicting_or_dense_single_traversal_cannot_satisfy_cumulative_rule(self):
        aligned = self.points(self.straight())
        conflicting = self.points([[3.374 + index * .0002, 6.5181] for index in range(6)],
                                  start_seconds=60)
        conflict = analyse_cumulative_existing_segment([aligned, conflicting], self.segment)
        self.assertFalse(conflict["auto_verify"])
        self.assertEqual(conflict["classification"], "DISCREPANCY")
        dense = self.points([[3.374 + index * .00005, 6.518] for index in range(21)],
                            step_seconds=.5)
        one_walk = analyse_cumulative_existing_segment([dense], self.segment)
        self.assertEqual(len(one_walk["passes"]), 1)
        self.assertFalse(one_walk["auto_verify"])

    def test_two_finalized_reverse_passes_verify_and_need_disappears(self):
        survey = self.finalized_survey(self.straight())
        analyse_survey(survey)
        self.segment.refresh_from_db()
        self.assertEqual(self.segment.verification_state, VerificationState.UNVERIFIED)
        first_review = analyse_survey_dry_run(survey)["existing"][0]
        self.assertTrue(first_review["needs_confirmation"])
        survey2 = self.finalized_survey(self.straight(reverse=True), start_seconds=60)
        analyse_survey(survey2)
        self.segment.refresh_from_db()
        self.assertEqual(self.segment.verification_state, VerificationState.FIELD_VERIFIED)
        record = SegmentVerificationRecord.objects.get(segment=self.segment)
        self.assertIsNone(record.actor)
        final_review = analyse_survey_dry_run(survey2)["existing"][0]
        self.assertTrue(final_review["evidence_sufficient"])
        self.assertFalse(final_review["needs_confirmation"])

    def test_new_geometry_requires_a_wholly_post_creation_confirmation_pass(self):
        creation_time = self.now + timedelta(seconds=100)
        WalkableSegment.objects.filter(pk=self.segment.pk).update(created_at=creation_time)
        self.segment.refresh_from_db()
        discovery = self.finalized_survey(self.straight(), start_seconds=0)
        straddling = self.finalized_survey(self.straight(reverse=True), start_seconds=90)
        analyse_survey(discovery)
        analyse_survey(straddling)
        self.segment.refresh_from_db()
        self.assertEqual(self.segment.verification_state, VerificationState.UNVERIFIED)
        pending = analyse_survey_dry_run(straddling)["existing"][0]
        self.assertFalse(pending["auto_verify"])
        self.assertFalse(pending["evidence_sufficient"])
        self.assertTrue(pending["needs_confirmation"])
        self.assertTrue(pending["temporal_confirmation_required"])

        confirmation = self.finalized_survey(self.straight(), start_seconds=130)
        analyse_survey(confirmation)
        self.segment.refresh_from_db()
        self.assertEqual(self.segment.verification_state, VerificationState.FIELD_VERIFIED)

    def test_reviewed_counts_but_abandoned_and_rejected_evidence_do_not(self):
        reviewed = self.finalized_survey(self.straight(), status=PathSurvey.Status.REVIEWED)
        abandoned = self.finalized_survey(self.straight(reverse=True),
                                          status=PathSurvey.Status.ABANDONED,
                                          start_seconds=60)
        rejected = self.finalized_survey(self.straight(reverse=True), start_seconds=120,
                                         rejected=True)
        result = analyse_survey_dry_run(reviewed)["existing"][0]
        self.assertEqual(len(result["supporting_passes"]), 1)
        self.assertFalse(result["auto_verify"])
        self.assertEqual(abandoned.status, PathSurvey.Status.ABANDONED)
        self.assertTrue(rejected.samples.filter(
            classification=PathSurveySample.Classification.REJECTED).exists())

    def test_one_good_and_one_poor_pass_do_not_verify(self):
        good = self.finalized_survey(self.straight())
        poor = self.finalized_survey(self.straight(reverse=True), start_seconds=60, accuracy=18)
        analyse_survey(good)
        analyse_survey(poor)
        self.segment.refresh_from_db()
        self.assertEqual(self.segment.verification_state, VerificationState.UNVERIFIED)
        result = analyse_survey_dry_run(poor)["existing"][0]
        self.assertEqual(len(result["supporting_passes"]), 1)
        self.assertTrue(result["needs_confirmation"])

    def test_later_bad_survey_never_revokes_verified_segment(self):
        first = self.finalized_survey(self.straight())
        second = self.finalized_survey(self.straight(reverse=True), start_seconds=60)
        analyse_survey(first); analyse_survey(second)
        self.segment.refresh_from_db()
        self.assertEqual(self.segment.verification_state, VerificationState.FIELD_VERIFIED)
        bad = self.finalized_survey(
            [[3.374 + index * .0002, 6.5181] for index in range(6)],
            start_seconds=120,
        )
        analyse_survey(bad)
        self.segment.refresh_from_db()
        self.assertEqual(self.segment.verification_state, VerificationState.FIELD_VERIFIED)
        self.assertEqual(self.segment.verification_records.filter(action="GRANTED").count(), 1)
        result = analyse_survey_dry_run(bad)["existing"][0]
        self.assertTrue(result["needs_review"])
        self.assertFalse(result["auto_verify"])

    def test_reviewer_rejected_evidence_is_excluded_and_confirmed_discrepancy_blocks(self):
        first = self.finalized_survey(self.straight())
        analyse_survey(first)
        first_match = first.segment_matches.get(segment=self.segment)
        first_match.disposition = SurveySegmentMatch.Disposition.REJECTED
        first_match.save(update_fields=("disposition",))
        second = self.finalized_survey(self.straight(reverse=True), start_seconds=60)
        analyse_survey(second)
        self.segment.refresh_from_db()
        self.assertEqual(self.segment.verification_state, VerificationState.UNVERIFIED)
        result = analyse_survey_dry_run(second)["existing"][0]
        self.assertEqual(len(result["supporting_passes"]), 1)

        second_match = second.segment_matches.get(segment=self.segment)
        second_match.disposition = SurveySegmentMatch.Disposition.DISCREPANCY_CONFIRMED
        second_match.save(update_fields=("disposition",))
        result = analyse_survey_dry_run(second)["existing"][0]
        self.assertTrue(result["review_blocked"])
        self.assertTrue(result["needs_review"])
        self.assertFalse(result["auto_verify"])

    def test_candidate_discovery_distinguishes_one_and_two_passes(self):
        far = [[3.378 + index*.00006, 6.521] for index in range(5)]
        one = discover_candidate_paths(self.points(far), [self.segment])
        self.assertEqual(len(one), 1)
        self.assertEqual((one[0]["pass_count"], one[0]["confirmed"]), (1, False))
        first = self.points(far)
        second = self.points(list(reversed(far)), start_seconds=60)
        two = discover_candidate_paths(first + second, [self.segment])
        self.assertEqual(len(two), 1)
        self.assertEqual((two[0]["pass_count"], two[0]["confirmed"]), (2, True))
        stationary = self.points([[3.378, 6.521], [3.378001, 6.521], [3.378, 6.521001],
                                  [3.378001, 6.521001], [3.378, 6.521]])
        self.assertEqual(candidate_runs(stationary, [self.segment]), [])

    def test_candidate_confirmation_matches_geometry_across_separate_surveys(self):
        far = [[3.378 + index*.00006, 6.521] for index in range(5)]
        candidates = discover_cumulative_candidate_paths([
            self.points(far),
            self.points(list(reversed(far)), start_seconds=90),
        ], [self.segment])
        self.assertEqual(len(candidates), 1)
        self.assertEqual((candidates[0]["pass_count"], candidates[0]["confirmed"]), (2, True))

    def test_loose_or_parallel_candidate_runs_do_not_gain_strict_confirmation(self):
        loose = [[3.378 + index*.00008, 6.521] for index in range(4)]
        candidates = discover_cumulative_candidate_paths([
            self.points(loose, accuracy=10),
            self.points(list(reversed(loose)), start_seconds=90, accuracy=10),
        ], [self.segment])
        self.assertEqual(len(candidates), 1)
        self.assertFalse(candidates[0]["confirmed"])
        self.assertEqual(candidates[0]["qualifying_pass_count"], 0)

        first = [[3.378 + index*.00006, 6.521] for index in range(5)]
        # Roughly three metres apart with five-metre fixes: this may be two
        # parallel paths and must not become automatic confirmation.
        parallel = [[value[0], value[1] + .000027] for value in first]
        separated = discover_cumulative_candidate_paths([
            self.points(first), self.points(parallel, start_seconds=90),
        ], [self.segment])
        self.assertEqual(len(separated), 2)
        self.assertTrue(all(not item["confirmed"] for item in separated))

    def test_dense_callbacks_are_one_candidate_pass_and_separate_corridors_stay_unconfirmed(self):
        dense = [[3.378 + index*.000015, 6.521] for index in range(18)]
        candidates = discover_candidate_paths(self.points(dense, step_seconds=.5), [self.segment])
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["pass_count"], 1)
        other = [[3.378 + index*.00006, 6.522] for index in range(5)]
        separated = discover_candidate_paths(
            self.points(dense, step_seconds=.5) + self.points(other, start_seconds=60), [self.segment])
        self.assertEqual(len(separated), 2)
        self.assertTrue(all(not item["confirmed"] for item in separated))

    def test_review_page_exposes_human_candidate_and_confirmation_worklist(self):
        survey = PathSurvey.objects.create(owner=self.editor, status=PathSurvey.Status.COMPLETED)
        far = [[3.378 + index*.00006, 6.521] for index in range(5)]
        PathSurveySample.objects.bulk_create([PathSurveySample(
            survey=survey, sequence=index+1, captured_at=self.now+timedelta(seconds=index*5),
            longitude=coordinate[0], latitude=coordinate[1], accuracy_metres=5,
            classification=PathSurveySample.Classification.ACCEPTED)
            for index, coordinate in enumerate(far)])
        self.client.force_login(self.editor)
        response = self.client.get(reverse("editor:survey-detail", args=(survey.pk,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "C1 — Possible unmapped path")
        self.assertContains(response, "Show only paths needing another walk")
        self.assertContains(response, reverse("editor:survey-candidate", args=(survey.pk, "C1")))
        self.assertContains(response, 'id="survey-candidate-data"', html=False)

    def test_confirmed_candidate_is_not_left_as_an_empty_confirmation_worklist(self):
        survey = PathSurvey.objects.create(owner=self.editor, status=PathSurvey.Status.COMPLETED)
        far = [[3.378 + index*.00006, 6.521] for index in range(5)]
        coordinates = far + list(reversed(far))
        PathSurveySample.objects.bulk_create([PathSurveySample(
            survey=survey, sequence=index+1,
            captured_at=self.now+timedelta(
                seconds=index*5 if index < len(far) else 60+(index-len(far))*5,
            ),
            longitude=coordinate[0], latitude=coordinate[1], accuracy_metres=5,
            classification=PathSurveySample.Classification.ACCEPTED,
        ) for index, coordinate in enumerate(coordinates)])
        self.client.force_login(self.editor)
        response = self.client.get(reverse("editor:survey-detail", args=(survey.pk,)))
        self.assertTrue(response.context["candidates"])
        self.assertEqual(response.context["confirmation_candidates"], [])
        self.assertContains(response, "No observed path currently needs another walk.")


class CandidateGraphCreationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.editor = get_user_model().objects.create_user("candidate-editor", password="test-password-42")
        cls.editor.user_permissions.add(*Permission.objects.filter(codename__in=(
            "add_walkablenode", "add_walkablesegment", "change_walkablesegment",
            "review_path_survey",
        )))

    def setUp(self):
        self.survey = PathSurvey.objects.create(owner=self.editor, status=PathSurvey.Status.COMPLETED)
        self.a = WalkableNode.objects.create(longitude=3.374, latitude=6.518,
                                              verification_state=VerificationState.UNVERIFIED)
        self.b = WalkableNode.objects.create(longitude=3.375, latitude=6.518,
                                              verification_state=VerificationState.UNVERIFIED)

    def candidate(self, confirmed=False):
        return {"id": "C1", "geometry": {"type": "LineString", "coordinates": [
            [3.37401, 6.518], [3.3745, 6.5182], [3.37499, 6.518]]},
            "length_metres": 115, "pass_count": 2 if confirmed else 1,
            "confirmed": confirmed, "reason": "test"}

    def strict_candidate(self):
        coordinates = [[3.37401 + index * .000196, 6.518] for index in range(6)]
        now = timezone.now()
        first = tuple(EvidencePoint(tuple(point), now + timedelta(seconds=index * 5), 5, index + 1)
                      for index, point in enumerate(coordinates))
        second = tuple(EvidencePoint(tuple(point), now + timedelta(seconds=60 + index * 5), 5, index + 1)
                       for index, point in enumerate(reversed(coordinates)))
        return discover_cumulative_candidate_paths([first, second], [])[0]

    def test_preview_is_read_only_and_creation_reuses_nodes_without_duplicates(self):
        before = (WalkableNode.objects.count(), WalkableSegment.objects.count())
        preview = preview_candidate_graph_change(self.candidate())
        self.assertEqual((preview["start"]["action"], preview["end"]["action"]),
                         ("reuse-node", "reuse-node"))
        self.assertEqual(preview["start"]["action_label"], "Connect to an existing junction")
        self.assertEqual(before, (WalkableNode.objects.count(), WalkableSegment.objects.count()))
        segment = create_candidate_path(survey=self.survey, candidate=self.candidate(), actor=self.editor)
        self.assertEqual(segment.verification_state, VerificationState.UNVERIFIED)
        self.assertEqual(WalkableNode.objects.count(), 2)
        with self.assertRaises(ValidationError):
            create_candidate_path(survey=self.survey, candidate=self.candidate(), actor=self.editor)
        self.assertEqual(WalkableSegment.objects.count(), 1)

    @patch("locations.editor_views.analyse_survey_dry_run")
    def test_candidate_http_flow_is_read_only_until_explicit_confirmed_post(self, analyse):
        analyse.return_value = {"candidates": [self.candidate()]}
        self.client.force_login(self.editor)
        url = reverse("editor:survey-candidate", args=(self.survey.pk, "C1"))
        before = (WalkableNode.objects.count(), WalkableSegment.objects.count())

        preview = self.client.get(url)
        self.assertEqual(preview.status_code, 200)
        self.assertEqual((WalkableNode.objects.count(), WalkableSegment.objects.count()), before)

        unconfirmed = self.client.post(url, {})
        self.assertEqual(unconfirmed.status_code, 200)
        self.assertEqual((WalkableNode.objects.count(), WalkableSegment.objects.count()), before)

        fingerprint = preview.context["preview"]["candidate_fingerprint"]
        created = self.client.post(url, {"confirm": "yes", "candidate_fingerprint": fingerprint})
        self.assertEqual(created.status_code, 302)
        segment = WalkableSegment.objects.get()
        target = reverse("editor:segment-edit", args=(segment.pk,))
        self.assertEqual(created.headers["Location"], target)
        self.assertEqual(self.client.get(target).status_code, 200)
        self.assertEqual(analyse.call_count, 3,
                         "each request must recompute the candidate against the current graph")

    @patch("locations.editor_views.analyse_survey_dry_run")
    def test_candidate_creation_requires_permission_and_csrf(self, analyse):
        analyse.return_value = {"candidates": [self.candidate()]}
        url = reverse("editor:survey-candidate", args=(self.survey.pk, "C1"))
        before = (WalkableNode.objects.count(), WalkableSegment.objects.count())

        unauthorized = get_user_model().objects.create_user("candidate-viewer", password="test-password-42")
        self.client.force_login(unauthorized)
        self.assertEqual(self.client.get(url).status_code, 403)

        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.editor)
        self.assertEqual(csrf_client.post(url, {"confirm": "yes"}).status_code, 403)
        self.assertEqual((WalkableNode.objects.count(), WalkableSegment.objects.count()), before)

    @patch("locations.editor_views.analyse_survey_dry_run")
    def test_graph_editor_without_survey_review_permission_cannot_access_private_candidate(self, analyse):
        analyse.return_value = {"candidates": [self.candidate()]}
        graph_only = get_user_model().objects.create_user("graph-only", password="test-password-42")
        graph_only.user_permissions.add(*Permission.objects.filter(codename__in=(
            "add_walkablenode", "add_walkablesegment", "change_walkablesegment",
        )))
        self.client.force_login(graph_only)
        url = reverse("editor:survey-candidate", args=(self.survey.pk, "C1"))
        before = (WalkableNode.objects.count(), WalkableSegment.objects.count())
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {"confirm": "yes"}).status_code, 403)
        self.assertEqual((WalkableNode.objects.count(), WalkableSegment.objects.count()), before)
        analyse.assert_not_called()

    def test_two_independent_passes_may_create_verified_geometry(self):
        loose = create_candidate_path(survey=self.survey, candidate=self.candidate(True), actor=self.editor)
        self.assertEqual(loose.verification_state, VerificationState.UNVERIFIED,
                         "a caller-supplied confirmed flag is not verification evidence")
        loose.is_active = False
        loose.save(update_fields=("is_active",))
        segment = create_candidate_path(survey=self.survey, candidate=self.strict_candidate(), actor=self.editor)
        self.assertEqual(segment.verification_state, VerificationState.FIELD_VERIFIED)
        self.assertTrue(segment.verification_records.filter(action="GRANTED").exists())

    @patch("locations.editor_views.analyse_survey_dry_run")
    def test_candidate_confirmation_rejects_a_reordered_or_changed_preview(self, analyse):
        original = self.candidate()
        analyse.return_value = {"candidates": [original]}
        self.client.force_login(self.editor)
        url = reverse("editor:survey-candidate", args=(self.survey.pk, "C1"))
        preview = self.client.get(url)
        old_fingerprint = preview.context["preview"]["candidate_fingerprint"]
        changed = {**original, "geometry": {"type": "LineString", "coordinates": [
            [3.37401, 6.5182], [3.3745, 6.5183], [3.37499, 6.5182],
        ]}}
        analyse.return_value = {"candidates": [changed]}
        before = (WalkableNode.objects.count(), WalkableSegment.objects.count())
        response = self.client.post(url, {
            "confirm": "yes", "candidate_fingerprint": old_fingerprint,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "candidate changed since preview")
        self.assertEqual((WalkableNode.objects.count(), WalkableSegment.objects.count()), before)

    @patch("locations.editor_views.analyse_survey_dry_run")
    def test_candidate_confirmation_rejects_changed_evidence_with_same_geometry(self, analyse):
        strict = self.strict_candidate()
        one_pass = {
            **strict,
            "passes": strict["passes"][:1],
            "pass_count": 1,
            "qualifying_pass_count": 1,
            "confirmed": False,
            "verification_ready": False,
        }
        analyse.return_value = {"candidates": [one_pass]}
        self.client.force_login(self.editor)
        url = reverse("editor:survey-candidate", args=(self.survey.pk, "C1"))
        preview = self.client.get(url)
        old_token = preview.context["preview"]["candidate_fingerprint"]

        analyse.return_value = {"candidates": [strict]}
        response = self.client.post(url, {
            "confirm": "yes", "candidate_fingerprint": old_token,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "candidate changed since preview")
        self.assertFalse(WalkableSegment.objects.exists())

    def test_joining_middle_of_existing_segment_uses_transactional_split(self):
        existing = WalkableSegment.objects.create(start_node=self.a, end_node=self.b,
            geometry={"type": "LineString", "coordinates": [[3.374, 6.518], [3.375, 6.518]]},
            verification_state=VerificationState.UNVERIFIED)
        candidate = {"id": "C2", "geometry": {"type": "LineString", "coordinates": [
            [3.3745, 6.51801], [3.3745, 6.5183], [3.3745, 6.5186]]},
            "length_metres": 66, "pass_count": 1, "confirmed": False, "reason": "test"}
        preview = preview_candidate_graph_change(candidate)
        self.assertEqual(preview["start"]["action"], "split-segment")
        created = create_candidate_path(survey=self.survey, candidate=candidate, actor=self.editor)
        existing.refresh_from_db()
        self.assertFalse(existing.is_active)
        self.assertEqual(created.verification_state, VerificationState.UNVERIFIED)
        self.assertEqual(WalkableSegment.objects.filter(is_active=True).count(), 3)

    def test_creation_adds_only_required_nodes_and_failed_same_node_resolution_rolls_back(self):
        candidate = {"id": "C3", "geometry": {"type": "LineString", "coordinates": [
            [3.378, 6.521], [3.3782, 6.5211], [3.3784, 6.5212]]},
            "length_metres": 50, "pass_count": 1, "confirmed": False, "reason": "test"}
        preview = preview_candidate_graph_change(candidate)
        self.assertEqual((preview["start"]["action"], preview["end"]["action"]),
                         ("create-node", "create-node"))
        create_candidate_path(survey=self.survey, candidate=candidate, actor=self.editor)
        self.assertEqual((WalkableNode.objects.count(), WalkableSegment.objects.count()), (4, 1))

        same_node = {"id": "C4", "geometry": {"type": "LineString", "coordinates": [
            [3.374001, 6.518], [3.374002, 6.518001], [3.374003, 6.518]]},
            "length_metres": 1, "pass_count": 1, "confirmed": False, "reason": "test"}
        before = (WalkableNode.objects.count(), WalkableSegment.objects.count())
        with self.assertRaises(ValidationError):
            create_candidate_path(survey=self.survey, candidate=same_node, actor=self.editor)
        self.assertEqual((WalkableNode.objects.count(), WalkableSegment.objects.count()), before)
