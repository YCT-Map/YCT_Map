from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q

from .editor_services import split_segment
from .geometry import coordinates, distance_metres
from .matching import project_onto_segment
from .models import (PathSurvey, SegmentVerificationRecord, SourceType, VerificationState,
                     WalkableNode, WalkableSegment)
from .survey_analysis import (candidate_confirmation_token, candidate_fingerprint,
                              candidate_has_strict_confirmation)


CANDIDATE_NODE_REUSE_METRES = 5.0
CANDIDATE_SEGMENT_JOIN_METRES = 5.0


def _nearest_node(point):
    choices = [(distance_metres(point, (float(node.longitude), float(node.latitude))), node)
               for node in WalkableNode.objects.filter(is_active=True)]
    return min(choices, key=lambda item: (item[0], str(item[1].pk)), default=(float("inf"), None))


def _nearest_segment(point):
    choices = [(projection.distance_metres, segment, projection)
               for segment in WalkableSegment.objects.filter(is_active=True).select_related("start_node", "end_node")
               for projection in (project_onto_segment(point, segment),)]
    return min(choices, key=lambda item: (item[0], str(item[1].pk)),
               default=(float("inf"), None, None))


def _endpoint_preview(point):
    node_distance, node = _nearest_node(point)
    if node and node_distance <= CANDIDATE_NODE_REUSE_METRES:
        return {"action": "reuse-node", "node_id": str(node.pk), "label": str(node),
                "distance_metres": round(node_distance, 1)}
    segment_distance, segment, projection = _nearest_segment(point)
    if segment and segment_distance <= CANDIDATE_SEGMENT_JOIN_METRES:
        endpoint_distance = min(projection.distance_to_start, projection.distance_to_end)
        if endpoint_distance >= 1:
            return {"action": "split-segment", "segment_id": str(segment.pk),
                    "label": segment.label or str(segment.pk),
                    "distance_metres": round(segment_distance, 1),
                    "coordinate": list(projection.coordinate)}
    return {"action": "create-node", "coordinate": list(point), "distance_metres": None}


def preview_candidate_graph_change(candidate):
    points = coordinates(candidate["geometry"])
    start = _endpoint_preview(points[0])
    end = _endpoint_preview(points[-1])
    action_labels = {
        "reuse-node": "Connect to an existing junction",
        "split-segment": "Join an existing path at a new junction",
        "create-node": "Create a new connection point",
    }
    start = {**start, "action_label": action_labels[start["action"]]}
    end = {**end, "action_label": action_labels[end["action"]]}
    verification_ready = candidate_has_strict_confirmation(candidate)
    verification_state = (VerificationState.FIELD_VERIFIED
                          if verification_ready else VerificationState.UNVERIFIED)
    return {
        "candidate_id": candidate["id"],
        # Keep the existing form-field contract while binding the token to the
        # evidence and resulting verification state, not geometry alone.
        "candidate_fingerprint": candidate_confirmation_token(candidate),
        "length_metres": candidate["length_metres"],
        "pass_count": candidate["pass_count"],
        "verification_state": verification_state,
        "verification_label": VerificationState(verification_state).label,
        "start": start,
        "end": end,
        "warnings": [item for item in (
            "An existing path will be split transactionally." if "split-segment" in {start["action"], end["action"]} else None,
            "A new routing node will be created." if "create-node" in {start["action"], end["action"]} else None,
            "A second strict independent walk is still required."
            if not verification_ready else None,
        ) if item],
    }


def _resolve_endpoint(point, actor):
    node_distance, node = _nearest_node(point)
    if node and node_distance <= CANDIDATE_NODE_REUSE_METRES:
        return node
    segment_distance, segment, projection = _nearest_segment(point)
    if segment and segment_distance <= CANDIDATE_SEGMENT_JOIN_METRES:
        if min(projection.distance_to_start, projection.distance_to_end) >= 1:
            node, _, _ = split_segment(segment, projection.coordinate, actor)
            return node
    node = WalkableNode(
        label="Survey candidate connection",
        longitude=Decimal(f"{point[0]:.6f}"), latitude=Decimal(f"{point[1]:.6f}"),
        source_type=SourceType.MANUAL,
        source_reference="path-survey-candidate",
        verification_state=VerificationState.UNVERIFIED,
        created_by=actor, updated_by=actor,
    )
    node.full_clean(); node.save()
    return node


@transaction.atomic
def create_candidate_path(*, survey, candidate, actor):
    """Apply an explicitly approved preview; never called during analysis."""
    survey = PathSurvey.objects.select_for_update().get(pk=survey.pk)
    fingerprint = candidate.get("fingerprint") or candidate_fingerprint(candidate["geometry"])
    source_reference = f"survey:{survey.pk}:{fingerprint[:16]}"
    if WalkableSegment.objects.filter(source_reference=source_reference).exists():
        raise ValidationError("This survey candidate has already been added to the routing graph.")
    # Serialize endpoint resolution against concurrent graph edits so two
    # confirmations cannot independently create the same junction/segment.
    list(WalkableNode.objects.select_for_update().filter(is_active=True).values_list("pk", flat=True))
    list(WalkableSegment.objects.select_for_update().filter(is_active=True).values_list("pk", flat=True))
    raw_points = coordinates(candidate["geometry"])
    start_node = _resolve_endpoint(raw_points[0], actor)
    end_node = _resolve_endpoint(raw_points[-1], actor)
    if start_node.pk == end_node.pk:
        raise ValidationError("Candidate endpoints resolve to the same routing node.")
    duplicate = WalkableSegment.objects.filter(is_active=True).filter(
        Q(start_node=start_node, end_node=end_node) | Q(start_node=end_node, end_node=start_node)
    ).exists()
    if duplicate:
        raise ValidationError("An active segment already connects these routing nodes.")
    geometry_points = [list(point) for point in raw_points]
    geometry_points[0] = [float(start_node.longitude), float(start_node.latitude)]
    geometry_points[-1] = [float(end_node.longitude), float(end_node.latitude)]
    state = (VerificationState.FIELD_VERIFIED
             if candidate_has_strict_confirmation(candidate) else VerificationState.UNVERIFIED)
    segment = WalkableSegment(
        label=f"Survey candidate {candidate['id']}",
        start_node=start_node, end_node=end_node,
        geometry={"type": "LineString", "coordinates": geometry_points},
        is_bidirectional=True,
        source_type=SourceType.MANUAL,
        source_reference=source_reference,
        verification_state=state,
        created_by=actor, updated_by=actor,
    )
    segment.full_clean(); segment.save()
    if state == VerificationState.FIELD_VERIFIED:
        SegmentVerificationRecord.objects.create(
            segment=segment,
            action=SegmentVerificationRecord.Action.GRANTED,
            geometry_revision=segment.geometry_revision,
            geometry_fingerprint=segment.geometry_fingerprint,
            actor=actor,
            reason=("Candidate was explicitly approved and already had at least two independent "
                    "high-quality passes in immutable survey evidence."),
        )
    return segment
