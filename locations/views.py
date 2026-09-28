"""Public Phase 1 map and location endpoints."""

from django.db.models import Q
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import ensure_csrf_cookie

from .models import InternalPlace, Location
from routing.destinations import resolve_destination


MAP_CENTRE = {"longitude": 3.37424, "latitude": 6.51857}
MAP_STYLE_URL = "https://tiles.openfreemap.org/styles/liberty"
MAPLIBRE_VERSION = "6.10.0"
UI_ASSET_VERSION = "destination-density-1"


def _routing_state(destination_key):
    resolution = resolve_destination(destination_key)
    return resolution.routing_available, resolution.unavailable_reason


def _internal_payload(place):
    routing_available, reason = _routing_state(f"internal:{place.id}")
    return {
        "id": str(place.id),
        "destination_key": f"internal:{place.id}",
        "destination_type": "internal",
        "name": place.name,
        "internal_type": place.internal_type,
        "internal_type_label": place.get_internal_type_display(),
        "parent": {"id": str(place.location_id), "name": place.location.name},
        "floor": {"id": str(place.floor_id), "label": place.floor.label, "level": place.floor.level} if place.floor_id else None,
        "room_code": place.room_code,
        "wing_section": place.wing_section,
        "direction_note": place.direction_note,
        "verification_state": place.verification_state,
        "routing_available": routing_available,
        "routing_unavailable_reason": reason,
    }


@require_GET
@ensure_csrf_cookie
def map_view(request):
    return render(
        request,
        "map/index.html",
        {
            "map_centre": MAP_CENTRE,
            "map_style_url": MAP_STYLE_URL,
            "maplibre_version": MAPLIBRE_VERSION,
            "ui_asset_version": UI_ASSET_VERSION,
            "categories": Location.Category.choices,
            "debug_network_url": "/api/debug/walkable-network/" if settings.DEBUG else "",
            "debug_route_anchors_url": "/api/debug/route-anchors/" if settings.DEBUG else "",
            "debug_route_url": "/api/debug/route/" if settings.DEBUG else "",
            "route_url": "/api/routes/",
            "live_route_url": "/api/routes/from-position/",
            "contribution_url": "/api/contributions/",
        },
    )


@require_GET
def location_collection(request):
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()

    if len(query) > 100:
        return JsonResponse({"error": "Search query must be 100 characters or fewer."}, status=400)

    category_values = {choice.value for choice in Location.Category}
    if category and category not in category_values:
        return JsonResponse({"error": "Unknown location category."}, status=400)

    locations = Location.objects.filter(
        publication_status=Location.PublicationStatus.PUBLISHED,
        representative_latitude__isnull=False,
        representative_longitude__isnull=False,
    ).prefetch_related("aliases", "categories").select_related("network_anchor__node")
    if query:
        locations = locations.filter(
            Q(name__icontains=query) | Q(aliases__name__icontains=query)
        ).distinct()
    if category:
        locations = locations.filter(category=category)

    features = []
    for location in locations:
        routing_available, routing_reason = _routing_state(f"location:{location.id}")
        features.append(
            {
                "type": "Feature",
                "id": str(location.id),
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(location.representative_longitude), float(location.representative_latitude)],
                },
                "properties": {
                    "id": str(location.id),
                    "destination_key": f"location:{location.id}",
                    "destination_type": "location",
                    "name": location.name,
                    "category": location.category,
                    "category_label": location.get_category_display(),
                    "description": location.description,
                    "verification_state": location.verification_state,
                    "verification_label": location.get_verification_state_display(),
                    "aliases": list(location.aliases.values_list("name", flat=True)),
                    "categories": [
                        {"slug": item.slug, "name": item.name}
                        for item in location.categories.all()
                    ],
                    "place_type": location.place_type,
                    "place_type_label": location.get_place_type_display(),
                    "routing_available": routing_available,
                    "routing_unavailable_reason": routing_reason,
                    "places_inside_count": location.internal_places.filter(
                        publication_status=Location.PublicationStatus.PUBLISHED,
                    ).count(),
                },
            }
        )

    response = JsonResponse(
        {
            "type": "FeatureCollection",
            "features": features,
            "meta": {
                "count": len(features),
                "query": query,
                "category": category,
            },
        }
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@require_GET
def destination_search(request):
    query = request.GET.get("q", "").strip()
    if len(query) > 100:
        return JsonResponse({"error": "Search query must be 100 characters or fewer."}, status=400)
    outdoor = Location.objects.filter(publication_status=Location.PublicationStatus.PUBLISHED)
    internal = InternalPlace.objects.filter(
        publication_status=Location.PublicationStatus.PUBLISHED,
        location__publication_status=Location.PublicationStatus.PUBLISHED,
    ).select_related("location", "floor", "routing_entrance").prefetch_related("aliases")
    if query:
        outdoor = outdoor.filter(Q(name__icontains=query) | Q(aliases__name__icontains=query)).distinct()
        internal = internal.filter(
            Q(name__icontains=query) | Q(aliases__name__icontains=query) |
            Q(room_code__icontains=query) | Q(location__name__icontains=query)
        ).distinct()
    results = [{
        "id": str(item.id), "destination_key": f"location:{item.id}", "destination_type": "location",
        "name": item.name, "subtitle": item.get_place_type_display(),
        "routing_available": _routing_state(f"location:{item.id}")[0],
        "routing_unavailable_reason": _routing_state(f"location:{item.id}")[1],
    } for item in outdoor[:50]]
    for item in internal[:50]:
        payload = _internal_payload(item)
        payload["subtitle"] = " · ".join(filter(None, [item.location.name, item.floor.label if item.floor_id else "", item.room_code]))
        results.append(payload)
    response = JsonResponse({"results": results, "meta": {"count": len(results), "query": query}})
    response.headers["Cache-Control"] = "no-store"
    return response


@require_GET
def internal_place_directory(request, location_id):
    location = Location.objects.filter(pk=location_id, publication_status=Location.PublicationStatus.PUBLISHED).first()
    if not location:
        return JsonResponse({"error": "Place not found."}, status=404)
    places = InternalPlace.objects.filter(
        location=location, publication_status=Location.PublicationStatus.PUBLISHED,
    ).select_related("location", "floor", "routing_entrance").order_by("floor__display_order", "floor__level", "name")
    groups = {}
    for place in places:
        label = place.floor.label if place.floor_id else "Floor not specified"
        groups.setdefault(label, []).append(_internal_payload(place))
    response = JsonResponse({"location": {"id": str(location.id), "name": location.name},
                             "floors": [{"label": label, "places": items} for label, items in groups.items()]})
    response.headers["Cache-Control"] = "no-store"
    return response
