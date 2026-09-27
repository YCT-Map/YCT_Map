"""URL configuration for YCT Map."""

from django.contrib import admin
from django.urls import include, path

from .views import health_check


urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("admin/", admin.site.urls),
    path("editor/", include("locations.editor_urls")),
    path("", include("locations.urls")),
    path("", include("routing.urls")),
    path("", include("contributions.urls")),
]
