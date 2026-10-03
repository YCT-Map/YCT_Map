import math
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from .geometry import distance_metres
from .matching import project_onto_segment
from .models import (PathSurvey, PathSurveySample, SegmentVerificationRecord,
                     SurveySegmentMatch, VerificationState, WalkableSegment)
from .survey_analysis import (analyse_cumulative_existing_segment,
                              analyse_existing_segments,
                              discover_cumulative_candidate_paths,
                              evidence_points)

GOOD_ACCURACY_METRES = 25
MAX_MATCH_ACCURACY_METRES = 50
MAX_WALKING_SPEED_METRES_PER_SECOND = 4.5
NEAR_DUPLICATE_METRES = 1.0
REDUNDANT_SAMPLE_MAX_SECONDS = 5.0
REDUNDANT_RADIUS_ACCURACY_FACTOR = 0.35
REDUNDANT_RADIUS_MAX_METRES = 4.0
MATCH_DISTANCE_METRES = 18
COORDINATE_PRECISION = Decimal("0.000001")
MEASUREMENT_PRECISION = Decimal("0.01")

TRANSITIONS = {
    PathSurvey.Status.DRAFT: {PathSurvey.Status.ACTIVE, PathSurvey.Status.ABANDONED},
    PathSurvey.Status.ACTIVE: {PathSurvey.Status.PAUSED, PathSurvey.Status.COMPLETED, PathSurvey.Status.ABANDONED},
    PathSurvey.Status.PAUSED: {PathSurvey.Status.ACTIVE, PathSurvey.Status.COMPLETED, PathSurvey.Status.ABANDONED},
    PathSurvey.Status.COMPLETED: {PathSurvey.Status.REVIEWED},
}
FINALIZED_SURVEY_STATUSES = (PathSurvey.Status.COMPLETED, PathSurvey.Status.REVIEWED)


def _cumulative_assessments(point_sets, segments):
    """Apply durable human evidence decisions to cumulative segment analysis."""
    constraints = {}
    reviewed_matches = SurveySegmentMatch.objects.filter(
        survey__status__in=FINALIZED_SURVEY_STATUSES,
        disposition__in=(
            SurveySegmentMatch.Disposition.REJECTED,
            SurveySegmentMatch.Disposition.DISCREPANCY_CONFIRMED,
        ),
    ).select_related("segment")
    for match in reviewed_matches:
        if (match.segment_revision != match.segment.geometry_revision or
                match.segment_fingerprint != match.segment.geometry_fingerprint):
            continue
        state = constraints.setdefault(match.segment_id, {"excluded_surveys": set(), "conflict": False})
        state["excluded_surveys"].add(match.survey_id)
        if match.disposition == SurveySegmentMatch.Disposition.DISCREPANCY_CONFIRMED:
            state["conflict"] = True

    results = []
    for segment in segments:
        state = constraints.get(segment.pk, {"excluded_surveys": set(), "conflict": False})
        eligible_sets = tuple(
            points for points in point_sets
            if points and points[0].survey_id not in state["excluded_surveys"]
        )
        assessment = analyse_cumulative_existing_segment(eligible_sets, segment, segments)
        supporting = assessment.get("supporting_passes", ())
        if assessment.get("auto_verify") and supporting:
            earliest = min(item.points[0].captured_at for item in supporting)
            existed_before_evidence = segment.created_at <= earliest
            has_post_creation_confirmation = any(
                item.points[0].captured_at >= segment.created_at for item in supporting
            )
            if not (existed_before_evidence or has_post_creation_confirmation):
                assessment = {
                    **assessment,
                    "auto_verify": False,
                    "evidence_sufficient": False,
                    "needs_confirmation": True,
                    "temporal_confirmation_required": True,
                }
        if state["conflict"]:
            assessment = {
                **assessment,
                "classification": "DISCREPANCY",
                "auto_verify": False,
                "evidence_sufficient": False,
                "needs_confirmation": segment.verification_state != VerificationState.FIELD_VERIFIED,
                "needs_review": True,
                "review_blocked": True,
            }
        results.append(assessment)
    return results


@transaction.atomic
def transition_survey(survey, target, actor):
    survey = PathSurvey.objects.select_for_update().get(pk=survey.pk)
    if survey.owner_id != actor.pk and not actor.is_superuser:
        raise PermissionDenied("Only the survey owner may control this survey.")
    # Mobile browsers may replay a delayed Finish submission after the first
    # request has already completed. Exact completion replay is safe and must
    # not rerun analysis; every other invalid transition still fails normally.
    if survey.status == PathSurvey.Status.COMPLETED and target == PathSurvey.Status.COMPLETED:
        return survey
    if target not in TRANSITIONS.get(survey.status, set()):
        raise ValidationError(f"Cannot change survey from {survey.get_status_display()} to {target}.")
    survey.status = target
    now = timezone.now()
    if target == PathSurvey.Status.ACTIVE and not survey.started_at: survey.started_at = now
    if target == PathSurvey.Status.COMPLETED: survey.completed_at = now
    survey.save()
    if target == PathSurvey.Status.COMPLETED:
        analyse_survey(survey)
    return survey


def classify_sample(survey, *, sequence, captured_at, longitude, latitude, accuracy, speed=None, heading=None):
    accuracy = float(accuracy)
    classification, reason = PathSurveySample.Classification.ACCEPTED, ""
    if accuracy > MAX_MATCH_ACCURACY_METRES:
        classification, reason = PathSurveySample.Classification.REJECTED, "Accuracy exceeds 50 m."
    elif accuracy > GOOD_ACCURACY_METRES:
        classification = PathSurveySample.Classification.WEAK
    previous = survey.samples.exclude(
        classification=PathSurveySample.Classification.REJECTED
    ).order_by("-sequence").first()
    if previous and classification != PathSurveySample.Classification.REJECTED:
        seconds = (captured_at - previous.captured_at).total_seconds()
        metres = distance_metres((float(previous.longitude), float(previous.latitude)), (float(longitude), float(latitude)))
        reference_accuracy = min(float(previous.accuracy_metres), accuracy)
        redundant_radius = max(NEAR_DUPLICATE_METRES, min(
            REDUNDANT_RADIUS_MAX_METRES,
            reference_accuracy * REDUNDANT_RADIUS_ACCURACY_FACTOR,
        ))
        if seconds <= 0 or metres / seconds > MAX_WALKING_SPEED_METRES_PER_SECOND:
            classification, reason = PathSurveySample.Classification.REJECTED, "Implausible GPS jump."
        elif seconds <= REDUNDANT_SAMPLE_MAX_SECONDS and metres < redundant_radius:
            classification, reason = PathSurveySample.Classification.REJECTED, "Redundant high-frequency sample."
    return PathSurveySample(survey=survey, sequence=sequence, captured_at=captured_at,
        longitude=Decimal(str(longitude)).quantize(COORDINATE_PRECISION, rounding=ROUND_HALF_UP),
        latitude=Decimal(str(latitude)).quantize(COORDINATE_PRECISION, rounding=ROUND_HALF_UP),
        accuracy_metres=Decimal(str(accuracy)).quantize(MEASUREMENT_PRECISION, rounding=ROUND_HALF_UP),
        classification=classification, rejection_reason=reason,
        speed_metres_per_second=(Decimal(str(speed)).quantize(MEASUREMENT_PRECISION, rounding=ROUND_HALF_UP)
                                 if speed is not None else None),
        heading_degrees=(Decimal(str(heading)).quantize(MEASUREMENT_PRECISION, rounding=ROUND_HALF_UP)
                         if heading is not None else None))


def _quantized(value, precision):
    if value is None:
        return None
    return Decimal(str(value)).quantize(precision, rounding=ROUND_HALF_UP)


def _same_raw_evidence(existing, payload):
    """A repeated sequence is idempotent only when every raw observation field agrees."""
    return (
        existing.captured_at == payload["captured_at"]
        and existing.longitude == _quantized(payload["longitude"], COORDINATE_PRECISION)
        and existing.latitude == _quantized(payload["latitude"], COORDINATE_PRECISION)
        and existing.accuracy_metres == _quantized(payload["accuracy"], MEASUREMENT_PRECISION)
        and existing.speed_metres_per_second == _quantized(payload.get("speed"), MEASUREMENT_PRECISION)
        and existing.heading_degrees == _quantized(payload.get("heading"), MEASUREMENT_PRECISION)
    )


@transaction.atomic
def store_samples(survey, samples, actor):
    survey = PathSurvey.objects.select_for_update().get(pk=survey.pk)
    if survey.owner_id != actor.pk:
        raise ValidationError("Samples are accepted only from the survey owner.")
    may_add = survey.status in (PathSurvey.Status.ACTIVE, PathSurvey.Status.PAUSED)
    stored = []
    for payload in sorted(samples, key=lambda item: int(item["sequence"])):
        existing = survey.samples.filter(sequence=payload["sequence"]).first()
        if existing:
            if not _same_raw_evidence(existing, payload):
                raise ValidationError("A sample sequence cannot be reused for different raw evidence.")
            stored.append(existing)
            continue
        if not may_add:
            raise ValidationError("New samples are accepted only for an active or paused survey.")
        sample = classify_sample(survey, **payload)
        sample.full_clean(); sample.save(); stored.append(sample)
    return stored


def _coverage(segment, supported_points):
    points = segment.geometry["coordinates"]
    if len(points) < 2 or len(supported_points) < 2: return 0
    total = segment.distance_metres
    along = []
    for point in supported_points:
        cumulative = 0
        best = (float("inf"), 0)
        for start, end in zip(points, points[1:]):
            leg = distance_metres(start, end)
            # Local projection fraction is sufficient at campus scale.
            dx, dy = end[0] - start[0], end[1] - start[1]
            ratio = 0 if dx == dy == 0 else max(0, min(1, ((point[0]-start[0])*dx + (point[1]-start[1])*dy)/(dx*dx+dy*dy)))
            candidate = (distance_metres(point, (start[0]+ratio*dx, start[1]+ratio*dy)), cumulative + ratio*leg)
            best = min(best, candidate)
            cumulative += leg
        along.append(best[1])
    return min(100, (max(along) - min(along)) / total * 100) if total else 0


def _longest_nearby_run(trace, projections):
    runs, current = [], []
    for point, projection in zip(trace, projections):
        if projection.distance_metres <= MATCH_DISTANCE_METRES:
            current.append((point, projection))
        elif current:
            runs.append(current); current = []
    if current: runs.append(current)
    return max(runs, key=len, default=[])


@transaction.atomic
def analyse_survey(survey):
    """Persist this survey's matches, then evaluate cumulative finalized evidence."""
    SurveySegmentMatch.objects.filter(survey=survey).delete()
    samples = list(survey.samples.exclude(
        classification=PathSurveySample.Classification.REJECTED,
    ).order_by("captured_at", "sequence"))
    if len(samples) < 2:
        return []
    points = evidence_points(samples)
    segments = list(WalkableSegment.objects.filter(is_active=True).select_related("start_node", "end_node"))
    results = []
    current_assessments = analyse_existing_segments(points, segments)
    for assessment in current_assessments:
        segment, best = assessment["segment"], assessment["best"]
        if best is None:
            continue
        classification = getattr(SurveySegmentMatch.Classification, assessment["classification"])
        match = SurveySegmentMatch.objects.create(survey=survey, segment=segment,
            segment_revision=segment.geometry_revision, segment_fingerprint=segment.geometry_fingerprint,
            classification=classification,
            coverage_percent=Decimal(str(round(best.coverage_percent, 2))),
            mean_distance_metres=Decimal(str(round(best.mean_offset_metres, 2))))
        results.append(match)

    # Only paths observed by the survey that just completed are candidates for
    # mutation. Historical finalized surveys are read as corroborating evidence;
    # merely deploying or opening a review page cannot trigger this block.
    affected_ids = {
        assessment["segment"].pk for assessment in current_assessments
        if assessment["best"] is not None
    }
    point_sets = finalized_evidence_point_sets()
    cumulative = _cumulative_assessments(point_sets, segments)
    matches_by_segment = {match.segment_id: match for match in results}
    for assessment in cumulative:
        segment = assessment["segment"]
        if segment.pk not in affected_ids or not assessment["auto_verify"]:
            continue
        if segment.verification_state != VerificationState.UNVERIFIED:
            continue
        supporting = assessment["supporting_passes"]
        earliest = min(item.points[0].captured_at for item in supporting)
        existed_before_evidence = segment.created_at <= earliest
        has_confirmation_after_creation = any(
            item.points[0].captured_at >= segment.created_at for item in supporting
        )
        if not (existed_before_evidence or has_confirmation_after_creation):
            continue
        segment.verification_state = VerificationState.FIELD_VERIFIED
        segment.save(update_fields=("verification_state", "updated_at"))
        SegmentVerificationRecord.objects.create(
            segment=segment,
            survey_match=matches_by_segment.get(segment.pk),
            action=SegmentVerificationRecord.Action.GRANTED,
            geometry_revision=segment.geometry_revision,
            geometry_fingerprint=segment.geometry_fingerprint,
            actor=None,
            reason=(
                "Automatic grant: cumulative finalized field evidence supplied "
                f"{len(supporting)} independent, contiguous, high-quality passes "
                "without a competing-path conflict."
            ),
        )
    return results


def finalized_evidence_point_sets():
    """Load usable evidence once and retain each survey as an independent trace."""
    samples = PathSurveySample.objects.filter(
        survey__status__in=FINALIZED_SURVEY_STATUSES,
    ).exclude(
        classification=PathSurveySample.Classification.REJECTED,
    ).order_by("survey_id", "captured_at", "sequence")
    grouped = {}
    for sample in samples:
        grouped.setdefault(sample.survey_id, []).append(sample)
    return tuple(
        tuple(evidence_points(group))
        for group in grouped.values()
        if len(group) >= 2
    )


def analyse_survey_dry_run(survey):
    """Derive campus-wide finalized evidence without writing database state."""
    if survey.status not in FINALIZED_SURVEY_STATUSES:
        return {"existing": [], "candidates": []}
    point_sets = finalized_evidence_point_sets()
    segments = list(WalkableSegment.objects.filter(is_active=True).select_related("start_node", "end_node"))
    return {
        "existing": _cumulative_assessments(point_sets, segments),
        "candidates": discover_cumulative_candidate_paths(point_sets, segments),
    }


@transaction.atomic
def record_match_review(match, *, disposition, actor, reason):
    """Persist one reviewer-only evidence decision without touching the graph."""
    if not actor.has_perm("routing.review_path_survey"):
        raise PermissionDenied
    reason = reason.strip()
    if not reason:
        raise ValidationError("A review reason is required.")
    allowed = {
        SurveySegmentMatch.Disposition.USEFUL_PARTIAL,
        SurveySegmentMatch.Disposition.REJECTED,
        SurveySegmentMatch.Disposition.DISCREPANCY_CONFIRMED,
    }
    if disposition not in allowed:
        raise ValidationError("Choose a valid review disposition.")
    match = SurveySegmentMatch.objects.select_for_update().get(pk=match.pk)
    match.disposition = disposition
    match.reviewer_note = reason
    match.reviewed_by = actor
    match.reviewed_at = timezone.now()
    match.full_clean()
    match.save(update_fields=(
        "disposition", "reviewer_note", "reviewed_by", "reviewed_at",
    ))
    return match


@transaction.atomic
def decide_verification(match, *, grant, actor, reason):
    permission = "routing.grant_field_verified" if grant else "routing.revoke_field_verified"
    if not actor.has_perm(permission): raise PermissionDenied
    if not reason.strip(): raise ValidationError("A reason is required.")
    match = SurveySegmentMatch.objects.select_for_update().select_related("segment", "survey").get(pk=match.pk)
    segment = WalkableSegment.objects.select_for_update().get(pk=match.segment_id)
    if match.segment_revision != segment.geometry_revision or match.segment_fingerprint != segment.geometry_fingerprint:
        raise ValidationError("This evidence belongs to an older segment geometry revision.")
    if grant and float(match.coverage_percent) < 80 and "override" not in reason.lower():
        raise ValidationError("Coverage below 80% requires an explicit override reason.")
    segment.verification_state = VerificationState.FIELD_VERIFIED if grant else VerificationState.UNVERIFIED
    segment.save(update_fields=("verification_state", "updated_at"))
    match.disposition = SurveySegmentMatch.Disposition.ACCEPTED if grant else SurveySegmentMatch.Disposition.REJECTED
    match.reviewer_note = reason.strip()
    match.reviewed_by = actor
    match.reviewed_at = timezone.now()
    match.save(update_fields=(
        "disposition", "reviewer_note", "reviewed_by", "reviewed_at",
    ))
    SegmentVerificationRecord.objects.create(segment=segment, survey_match=match,
        action=SegmentVerificationRecord.Action.GRANTED if grant else SegmentVerificationRecord.Action.REVOKED,
        geometry_revision=segment.geometry_revision, geometry_fingerprint=segment.geometry_fingerprint,
        actor=actor, reason=reason)
    return segment
