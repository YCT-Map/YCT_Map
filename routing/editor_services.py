import math

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q

from locations.models import Entrance

from .geometry import coordinates, distance_metres
from .models import (EntranceNetworkAnchor, LocationNetworkAnchor, SegmentVerificationRecord,
                     SourceType, VerificationState, WalkableNode, WalkableSegment)


MATERIAL_SEGMENT_FIELDS = ("start_node_id", "end_node_id", "geometry", "is_bidirectional")

# Current active campus-graph spacing is approximately 23 m at the median and
# 39 m at the 75th percentile. Keep the normal band inside that observed
# spacing, permit a deliberately warned inspection band, and never suggest an
# arbitrarily distant node merely to make a destination routable.
NEARBY_ENTRANCE_NODE_METRES = 40
MAX_ENTRANCE_NODE_METRES = 75
MAX_ENTRANCE_NODE_CANDIDATES = 6


def _node_display_label(node):
    return node.display_label


def entrance_node_candidates(entrance):
    """Return a small, distance-ordered set of connected active graph nodes."""
    origin = (float(entrance.longitude), float(entrance.latitude))
    nodes = WalkableNode.objects.filter(is_active=True).filter(
        Q(outgoing_segments__is_active=True) | Q(incoming_segments__is_active=True)
    ).distinct()
    candidates = []
    for node in nodes:
        distance = distance_metres(origin, (float(node.longitude), float(node.latitude)))
        if distance <= MAX_ENTRANCE_NODE_METRES:
            candidates.append({
                "node": node,
                "distance_metres": distance,
                "distance_label": f"{distance:.1f} m",
                "distance_band": "nearby" if distance <= NEARBY_ENTRANCE_NODE_METRES else "questionable",
                "display_label": _node_display_label(node),
            })
    candidates.sort(key=lambda item: (item["distance_metres"], str(item["node"].pk)))
    return candidates[:MAX_ENTRANCE_NODE_CANDIDATES]


def entrance_candidate_map_data(entrance, candidates):
    node_ids = {item["node"].pk for item in candidates}
    segments = WalkableSegment.objects.filter(is_active=True).filter(
        Q(start_node_id__in=node_ids) | Q(end_node_id__in=node_ids)
    ).distinct()
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": segment.geometry,
                "properties": {"kind": "segment", "id": str(segment.pk)},
            }
            for segment in segments
        ] + [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(item["node"].longitude), float(item["node"].latitude)],
                },
                "properties": {
                    "kind": "candidate",
                    "id": str(item["node"].pk),
                    "label": item["display_label"],
                    "distance_metres": round(item["distance_metres"], 1),
                    "distance_label": item["distance_label"],
                    "distance_band": item["distance_band"],
                    "source_type": item["node"].source_type,
                    "source_reference": item["node"].source_reference,
                },
            }
            for item in candidates
        ],
    }


@transaction.atomic
def connect_entrance_to_node(*, entrance, node, connector_geometry):
    entrance = Entrance.objects.select_for_update().get(pk=entrance.pk)
    node = WalkableNode.objects.select_for_update().get(pk=node.pk)
    if not entrance.is_active:
        raise ValidationError("Only an active entrance can be connected to the walking network.")
    candidate_ids = {item["node"].pk for item in entrance_node_candidates(entrance)}
    if node.pk not in candidate_ids:
        raise ValidationError("Choose one of the suitable active routing nodes shown for this entrance.")
    anchor = EntranceNetworkAnchor.objects.select_for_update().filter(entrance=entrance).first()
    if anchor is None:
        anchor = EntranceNetworkAnchor(entrance=entrance)
    anchor.node = node
    anchor.connector_geometry = connector_geometry
    anchor.is_active = True
    anchor.verification_state = VerificationState.UNVERIFIED
    anchor.full_clean()
    anchor.save()
    return anchor


@transaction.atomic
def disconnect_entrance_from_network(*, entrance):
    anchor = EntranceNetworkAnchor.objects.select_for_update().filter(entrance=entrance, is_active=True).first()
    if anchor:
        anchor.is_active = False
        anchor.save(update_fields=("is_active", "updated_at"))
    return anchor


@transaction.atomic
def save_segment(*, segment, cleaned_data, actor):
    """The authoritative path for material segment mutation."""
    creating = segment._state.adding
    if not creating:
        current = WalkableSegment.objects.select_for_update().get(pk=segment.pk)
        proposed = {
            "start_node_id": cleaned_data["start_node"].pk,
            "end_node_id": cleaned_data["end_node"].pk,
            "geometry": cleaned_data["geometry"],
            "is_bidirectional": cleaned_data["is_bidirectional"],
        }
        material = any(getattr(current, field) != proposed[field] for field in MATERIAL_SEGMENT_FIELDS)
        segment.geometry_revision = current.geometry_revision + (1 if material else 0)
        if material and current.verification_state == VerificationState.FIELD_VERIFIED:
            SegmentVerificationRecord.objects.create(segment=current, action=SegmentVerificationRecord.Action.INVALIDATED,
                geometry_revision=current.geometry_revision, geometry_fingerprint=current.geometry_fingerprint,
                actor=actor, reason="Material routing geometry changed.")
        if material:
            segment.verification_state = VerificationState.UNVERIFIED
            segment.geometry_fingerprint = ""
    else:
        segment.source_type = SourceType.MANUAL
        segment.verification_state = VerificationState.UNVERIFIED
    segment.updated_by = actor
    if creating: segment.created_by = actor
    segment.full_clean(); segment.save()
    return segment


def segment_impact(segment):
    """Return concrete graph/anchor effects; never imply route usage from stored data."""
    others = WalkableSegment.objects.filter(is_active=True).exclude(pk=segment.pk)
    endpoint_impacts = []
    for node in (segment.start_node, segment.end_node):
        degree_after = others.filter(Q(start_node=node) | Q(end_node=node)).count()
        entrance_count = EntranceNetworkAnchor.objects.filter(node=node, is_active=True).count()
        location_count = LocationNetworkAnchor.objects.filter(node=node, is_active=True).count()
        endpoint_impacts.append({"node": node, "degree_after": degree_after,
                                 "entrance_anchors": entrance_count, "location_anchors": location_count})
    return endpoint_impacts


def _project(point, start, end):
    latitude_scale = 111_320
    longitude_scale = latitude_scale * math.cos(math.radians(point[1]))
    px, py = point[0] * longitude_scale, point[1] * latitude_scale
    ax, ay = start[0] * longitude_scale, start[1] * latitude_scale
    bx, by = end[0] * longitude_scale, end[1] * latitude_scale
    dx, dy = bx - ax, by - ay
    ratio = 0 if dx == dy == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return (start[0] + ratio * (end[0] - start[0]), start[1] + ratio * (end[1] - start[1]))


@transaction.atomic
def split_segment(segment, point, actor):
    """Explicitly split one active segment while retaining the inactive original as audit history."""
    segment = WalkableSegment.objects.select_for_update().select_related("start_node", "end_node").get(pk=segment.pk)
    if not segment.is_active:
        raise ValidationError("Only an active segment can be split.")
    points = coordinates(segment.geometry)
    candidates = [(distance_metres(point, projected := _project(point, a, b)), index, projected)
                  for index, (a, b) in enumerate(zip(points, points[1:]))]
    distance, index, projected = min(candidates)
    if distance > 5:
        raise ValidationError("Choose a split point within 5 metres of this segment.")
    if min(distance_metres(projected, points[0]), distance_metres(projected, points[-1])) < 1:
        raise ValidationError("Choose a split point at least 1 metre from either endpoint.")
    node = WalkableNode.objects.create(longitude=projected[0], latitude=projected[1],
        source_type=SourceType.MANUAL, verification_state=VerificationState.UNVERIFIED, created_by=actor, updated_by=actor)
    first_points = points[:index + 1] + [projected]
    second_points = [projected] + points[index + 1:]
    common = dict(is_bidirectional=segment.is_bidirectional, source_type=SourceType.MANUAL,
                  source_reference=f"split:{segment.id}",
                  derived_from_segment=segment, verification_state=VerificationState.UNVERIFIED,
                  is_active=True, created_by=actor, updated_by=actor)
    first = WalkableSegment(start_node=segment.start_node, end_node=node,
        geometry={"type": "LineString", "coordinates": first_points}, **common)
    second = WalkableSegment(start_node=node, end_node=segment.end_node,
        geometry={"type": "LineString", "coordinates": second_points}, **common)
    first.full_clean(); first.save(); second.full_clean(); second.save()
    segment.is_active = False; segment.updated_by = actor; segment.save(update_fields=("is_active", "updated_by", "updated_at"))
    return node, first, second
