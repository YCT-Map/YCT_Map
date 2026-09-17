from django.urls import path

from . import views


app_name = "locations"

urlpatterns = [
    path("", views.map_view, name="map"),
    path("api/locations/", views.location_collection, name="collection"),
]
