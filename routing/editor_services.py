import math

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q

from .geometry import coordinates, distance_metres
from .models import EntranceNetworkAnchor, LocationNetworkAnchor, SourceType, VerificationState, WalkableNode, WalkableSegment


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
    node = WalkableNode.objects.create(label=f"Split of {segment.label or segment.pk}", longitude=projected[0], latitude=projected[1],
        source_type=SourceType.MANUAL, verification_state=VerificationState.UNVERIFIED, created_by=actor, updated_by=actor)
    first_points = points[:index + 1] + [projected]
    second_points = [projected] + points[index + 1:]
    common = dict(label=segment.label, is_bidirectional=segment.is_bidirectional, source_type=SourceType.MANUAL,
                  source_reference=f"split:{segment.id}",
                  verification_state=VerificationState.UNVERIFIED, is_active=True, created_by=actor, updated_by=actor)
    first = WalkableSegment(start_node=segment.start_node, end_node=node,
        geometry={"type": "LineString", "coordinates": first_points}, **common)
    second = WalkableSegment(start_node=node, end_node=segment.end_node,
        geometry={"type": "LineString", "coordinates": second_points}, **common)
    first.full_clean(); first.save(); second.full_clean(); second.save()
    segment.is_active = False; segment.updated_by = actor; segment.save(update_fields=("is_active", "updated_by", "updated_at"))
    return node, first, second
