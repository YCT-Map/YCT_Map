from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from routing.candidate_services import create_candidate_path, preview_candidate_graph_change
from routing.models import (PathSurvey, PathSurveySample, SegmentVerificationRecord,
                            VerificationState, WalkableNode, WalkableSegment)
from routing.survey_analysis import (EvidencePoint, analyse_existing_segment,
                                     candidate_runs, detect_segment_passes,
                                     discover_candidate_paths)
from routing.survey_services import analyse_survey


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
        self.assertTrue(analyse_existing_segment(trace, self.segment, [self.segment, parallel])["auto_verify"])
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

    def test_completion_auto_verifies_existing_geometry_once_and_never_downgrades(self):
        survey = PathSurvey.objects.create(owner=self.editor, status=PathSurvey.Status.COMPLETED)
        for index, coordinate in enumerate(self.straight()):
            PathSurveySample.objects.bulk_create([PathSurveySample(
                survey=survey, sequence=index+1, captured_at=self.now+timedelta(seconds=index*5),
                longitude=coordinate[0], latitude=coordinate[1], accuracy_metres=5,
                classification=PathSurveySample.Classification.ACCEPTED)])
        analyse_survey(survey)
        self.segment.refresh_from_db()
        self.assertEqual(self.segment.verification_state, VerificationState.FIELD_VERIFIED)
        record = SegmentVerificationRecord.objects.get(segment=self.segment)
        self.assertIsNone(record.actor)
        survey2 = PathSurvey.objects.create(owner=self.editor, status=PathSurvey.Status.COMPLETED)
        analyse_survey(survey2)
        self.segment.refresh_from_db()
        self.assertEqual(self.segment.verification_state, VerificationState.FIELD_VERIFIED)

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


class CandidateGraphCreationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.editor = get_user_model().objects.create_user("candidate-editor", password="test-password-42")

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

    def test_preview_is_read_only_and_creation_reuses_nodes_without_duplicates(self):
        before = (WalkableNode.objects.count(), WalkableSegment.objects.count())
        preview = preview_candidate_graph_change(self.candidate())
        self.assertEqual((preview["start"]["action"], preview["end"]["action"]),
                         ("reuse-node", "reuse-node"))
        self.assertEqual(before, (WalkableNode.objects.count(), WalkableSegment.objects.count()))
        segment = create_candidate_path(survey=self.survey, candidate=self.candidate(), actor=self.editor)
        self.assertEqual(segment.verification_state, VerificationState.UNVERIFIED)
        self.assertEqual(WalkableNode.objects.count(), 2)
        with self.assertRaises(ValidationError):
            create_candidate_path(survey=self.survey, candidate=self.candidate(), actor=self.editor)
        self.assertEqual(WalkableSegment.objects.count(), 1)

    def test_two_independent_passes_may_create_verified_geometry(self):
        segment = create_candidate_path(survey=self.survey, candidate=self.candidate(True), actor=self.editor)
        self.assertEqual(segment.verification_state, VerificationState.FIELD_VERIFIED)
        self.assertTrue(segment.verification_records.filter(action="GRANTED").exists())

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
