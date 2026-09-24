from django.urls import path

from . import views


app_name = "locations"

urlpatterns = [
    path("", views.map_view, name="map"),
    path("api/locations/", views.location_collection, name="collection"),
    path("api/search/", views.destination_search, name="search"),
    path("api/locations/<uuid:location_id>/internal-places/", views.internal_place_directory, name="internal-directory"),
]
