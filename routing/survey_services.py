import math
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from .geometry import distance_metres
from .matching import project_onto_segment
from .models import (PathSurvey, PathSurveySample, SegmentVerificationRecord,
                     SurveySegmentMatch, VerificationState, WalkableSegment)

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
    SurveySegmentMatch.objects.filter(survey=survey).delete()
    samples = list(survey.samples.exclude(classification=PathSurveySample.Classification.REJECTED))
    if len(samples) < 2: return []
    trace = [(float(x.longitude), float(x.latitude)) for x in samples]
    results = []
    for segment in WalkableSegment.objects.filter(is_active=True).select_related("start_node", "end_node"):
        projections = [project_onto_segment(point, segment) for point in trace]
        nearby = [match for match in projections if match.distance_metres <= MATCH_DISTANCE_METRES]
        if len(nearby) < 2: continue
        support = _longest_nearby_run(trace, projections)
        coverage = _coverage(segment, [point for point, _ in support])
        mean = sum(x.distance_metres for x in nearby) / len(nearby)
        if mean > 12: classification = SurveySegmentMatch.Classification.DISCREPANCY
        elif coverage >= 80 and len(nearby) / len(trace) >= .7: classification = SurveySegmentMatch.Classification.STRONG
        elif coverage >= 20: classification = SurveySegmentMatch.Classification.PARTIAL
        else: classification = SurveySegmentMatch.Classification.AMBIGUOUS
        results.append(SurveySegmentMatch.objects.create(survey=survey, segment=segment,
            segment_revision=segment.geometry_revision, segment_fingerprint=segment.geometry_fingerprint,
            classification=classification, coverage_percent=Decimal(str(round(coverage, 2))),
            mean_distance_metres=Decimal(str(round(mean, 2)))))
    return results


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
    match.reviewer_note = reason; match.save(update_fields=("disposition", "reviewer_note"))
    SegmentVerificationRecord.objects.create(segment=segment, survey_match=match,
        action=SegmentVerificationRecord.Action.GRANTED if grant else SegmentVerificationRecord.Action.REVOKED,
        geometry_revision=segment.geometry_revision, geometry_fingerprint=segment.geometry_fingerprint,
        actor=actor, reason=reason)
    return segment
