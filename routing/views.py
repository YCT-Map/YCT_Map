from django.conf import settings
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_GET

from .models import VerificationState, WalkableNode, WalkableSegment


@require_GET
def demo_network(request):
    if not settings.DEBUG:
        raise Http404
    nodes = WalkableNode.objects.filter(is_active=True, verification_state=VerificationState.DEMO)
    segments = WalkableSegment.objects.filter(is_active=True, verification_state=VerificationState.DEMO, start_node__is_active=True, end_node__is_active=True)
    features = [{"type": "Feature", "id": str(segment.id), "geometry": segment.geometry,
                 "properties": {"feature_type": "segment", "label": segment.label, "verification_state": segment.verification_state,
                                "is_bidirectional": segment.is_bidirectional, "distance_metres": round(segment.distance_metres, 2)}} for segment in segments]
    features += [{"type": "Feature", "id": str(node.id), "geometry": {"type": "Point", "coordinates": [float(node.longitude), float(node.latitude)]},
                  "properties": {"feature_type": "node", "label": node.label, "verification_state": node.verification_state}} for node in nodes]
    response = JsonResponse({"type": "FeatureCollection", "features": features,
                             "meta": {"purpose": "DEMO network inspection only", "route_calculated": False}})
    response.headers["Cache-Control"] = "no-store"
    return response
