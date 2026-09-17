"""URL configuration for YCT Map."""

from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("locations.urls")),
    path("", include("routing.urls")),
]
