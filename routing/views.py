from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import Http404, JsonResponse
import json

from django.views.decorators.http import require_GET, require_POST

from .eta import format_approximate_eta
from .models import LocationNetworkAnchor, VerificationState, WalkableNode, WalkableSegment
from .matching import InsufficientAccuracyError, LivePositionError, NoSafeNetworkMatchError
from .results import InvalidNodeError, MissingAnchorError, NoRouteError
from .services import route_between_locations, route_from_live_position, route_to_destination
from .destinations import destination_summary
from locations.models import Location


@require_GET
def demo_network(request):
    if not settings.DEBUG:
        raise Http404
    nodes = WalkableNode.objects.filter(is_active=True)
    segments = WalkableSegment.objects.filter(is_active=True, start_node__is_active=True, end_node__is_active=True)
    features = [{"type": "Feature", "id": str(segment.id), "geometry": segment.geometry,
                 "properties": {"feature_type": "segment", "label": segment.label, "verification_state": segment.verification_state,
                                "is_bidirectional": segment.is_bidirectional, "distance_metres": round(segment.distance_metres, 2)}} for segment in segments]
    features += [{"type": "Feature", "id": str(node.id), "geometry": {"type": "Point", "coordinates": [float(node.longitude), float(node.latitude)]},
                  "properties": {"feature_type": "node", "label": node.label, "verification_state": node.verification_state}} for node in nodes]
    response = JsonResponse({"type": "FeatureCollection", "features": features,
                             "meta": {"purpose": "DEMO network inspection only", "route_calculated": False}})
    response.headers["Cache-Control"] = "no-store"
    return response


def _require_debug():
    if not settings.DEBUG:
        raise Http404


@require_GET
def demo_route_anchors(request):
    _require_debug()
    anchors = LocationNetworkAnchor.objects.filter(
        is_active=True,
        location__publication_status=Location.PublicationStatus.PUBLISHED,
        node__is_active=True,
    ).select_related("location", "node").order_by("location__name")
    response = JsonResponse({
        "anchors": [{
            "location_id": str(anchor.location_id),
            "location_name": anchor.location.name,
            "node_id": str(anchor.node_id),
            "verification_state": anchor.verification_state,
        } for anchor in anchors],
        "meta": {"purpose": "DEMO route inspection only"},
    })
    response.headers["Cache-Control"] = "no-store"
    return response


@require_GET
def demo_route(request):
    _require_debug()
    origin_id = request.GET.get("origin", "").strip()
    destination_id = request.GET.get("destination", "").strip()
    if not origin_id or not destination_id:
        return JsonResponse({"error": "Both origin and destination identifiers are required."}, status=400)
    try:
        result = route_between_locations(origin_id, destination_id)
    except (ValidationError, ValueError, InvalidNodeError, MissingAnchorError) as error:
        return JsonResponse({"error": str(error)}, status=400)
    except NoRouteError as error:
        return JsonResponse({"error": str(error), "code": "NO_ROUTE"}, status=404)
    geometry = ({"type": "Point", "coordinates": result.geometry[0]} if len(result.geometry) == 1
                else {"type": "LineString", "coordinates": result.geometry})
    response = JsonResponse({
        "route": {
            "type": "Feature",
            "geometry": geometry,
            "properties": {
                "route_state": "DEMO" if result.verification_states == (VerificationState.DEMO,) else "MIXED",
                "origin_node_id": result.origin_node_id,
                "destination_node_id": result.destination_node_id,
                "node_ids": result.node_ids,
                "segment_ids": result.segment_ids,
                "distance_metres": round(result.distance_metres, 2),
                "eta_seconds": round(result.eta_seconds, 2),
                "eta_label": format_approximate_eta(result.eta_seconds),
                "verification_states": result.verification_states,
            },
        },
        "meta": {"purpose": "DEMO route inspection only", "route_calculated": True, "eta_is_approximate": True},
    })
    response.headers["Cache-Control"] = "no-store"
    return response


@require_GET
def public_route(request):
    origin_id = request.GET.get("origin", "").strip()
    destination_id = request.GET.get("destination", "").strip()
    if not origin_id or not destination_id:
        return JsonResponse({"error": "Choose both an origin and destination.", "code": "INVALID_REQUEST"}, status=400)
    if origin_id == destination_id:
        return JsonResponse({"error": "Your starting point and destination are the same.", "code": "SAME_ORIGIN"}, status=409)
    try:
        result, origin_resolution, destination_resolution = route_to_destination(origin_id, destination_id)
    except (ValidationError, ValueError, Location.DoesNotExist, InvalidNodeError) as error:
        return JsonResponse({"error": "The selected route endpoints are invalid.", "code": "INVALID_ENDPOINT"}, status=400)
    except MissingAnchorError as error:
        return JsonResponse({"error": str(error), "code": "MISSING_ANCHOR"}, status=422)
    except NoRouteError:
        return JsonResponse({"error": "No walkable route is available between these destinations.", "code": "NO_ROUTE"}, status=404)

    geometry = ({"type": "Point", "coordinates": result.geometry[0]} if len(result.geometry) == 1
                else {"type": "LineString", "coordinates": result.geometry})
    route_state = "DEMO" if result.verification_states == (VerificationState.DEMO,) else "UNVERIFIED"
    response = JsonResponse({
        "route": {"type": "Feature", "geometry": geometry, "properties": {"route_state": route_state}},
        "summary": {
            "origin": destination_summary(origin_resolution),
            "destination": destination_summary(destination_resolution),
            "distance_metres": round(result.distance_metres, 2),
            "eta_label": format_approximate_eta(result.eta_seconds),
            "eta_is_approximate": True,
            "verification_state": route_state,
        },
    })
    response.headers["Cache-Control"] = "no-store"
    return response


@require_POST
def public_route_from_position(request):
    try:
        payload = json.loads(request.body)
        position = payload["position"]
        destination_id = str(payload["destination"]).strip()
        longitude = position["longitude"]
        latitude = position["latitude"]
        accuracy_metres = position["accuracy_metres"]
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
        return JsonResponse({"error": "A valid destination and live position are required.", "code": "INVALID_POSITION"}, status=400)
    try:
        result, match, destination = route_from_live_position(
            longitude, latitude, accuracy_metres, destination_id,
        )
    except InsufficientAccuracyError as error:
        return JsonResponse({"error": str(error), "code": error.code}, status=422)
    except NoSafeNetworkMatchError as error:
        return JsonResponse({"error": str(error), "code": error.code}, status=422)
    except LivePositionError as error:
        return JsonResponse({"error": str(error), "code": error.code}, status=400)
    except MissingAnchorError as error:
        return JsonResponse({"error": str(error),
                             "code": "MISSING_DESTINATION_ANCHOR"}, status=422)
    except (ValidationError, ValueError, InvalidNodeError):
        return JsonResponse({"error": "The live route request is invalid.", "code": "INVALID_POSITION"}, status=400)
    except NoRouteError:
        return JsonResponse({"error": "No walkable route is available from this position.", "code": "NO_ROUTE"}, status=404)

    geometry = ({"type": "Point", "coordinates": result.geometry[0]} if len(result.geometry) == 1
                else {"type": "LineString", "coordinates": result.geometry})
    response = JsonResponse({
        "route": {"type": "Feature", "geometry": geometry, "properties": {"route_state": "UNVERIFIED", "origin_type": "live"}},
        "summary": {
            "origin": {"name": "Your location", "type": "live"},
            "destination": destination_summary(destination),
            "total_distance_metres": round(result.distance_metres, 2),
            "remaining_distance_metres": round(result.distance_metres, 2),
            "eta_label": format_approximate_eta(result.eta_seconds),
            "eta_is_approximate": True,
            "eta_source": "fallback",
            "verification_state": "UNVERIFIED",
            "network_match_distance_metres": round(match.distance_metres, 2),
        },
    })
    response.headers["Cache-Control"] = "no-store"
    return response
