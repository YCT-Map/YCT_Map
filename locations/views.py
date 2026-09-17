"""Public Phase 1 map and location endpoints."""

from django.db.models import Q
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from .models import Location


MAP_CENTRE = {"longitude": 3.37424, "latitude": 6.51857}
MAP_STYLE_URL = "https://tiles.openfreemap.org/styles/liberty"
MAPLIBRE_VERSION = "6.10.0"


@require_GET
def map_view(request):
    return render(
        request,
        "map/index.html",
        {
            "map_centre": MAP_CENTRE,
            "map_style_url": MAP_STYLE_URL,
            "maplibre_version": MAPLIBRE_VERSION,
            "categories": Location.Category.choices,
            "debug_network_url": "/api/debug/walkable-network/" if settings.DEBUG else "",
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

    locations = Location.objects.filter(is_active=True).prefetch_related("aliases")
    if query:
        locations = locations.filter(
            Q(name__icontains=query) | Q(aliases__name__icontains=query)
        ).distinct()
    if category:
        locations = locations.filter(category=category)

    features = []
    for location in locations:
        features.append(
            {
                "type": "Feature",
                "id": str(location.id),
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        float(location.entrance_longitude),
                        float(location.entrance_latitude),
                    ],
                },
                "properties": {
                    "id": str(location.id),
                    "name": location.name,
                    "category": location.category,
                    "category_label": location.get_category_display(),
                    "description": location.description,
                    "verification_state": location.verification_state,
                    "verification_label": location.get_verification_state_display(),
                    "aliases": list(location.aliases.values_list("name", flat=True)),
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
