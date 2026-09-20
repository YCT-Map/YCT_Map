from django.contrib.auth.views import LogoutView
from django.urls import path, reverse_lazy

from . import editor_views

app_name = "editor"

urlpatterns = [
    path("login/", editor_views.EditorLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page=reverse_lazy("editor:login")), name="logout"),
    path("", editor_views.dashboard, name="dashboard"),
    path("places/", editor_views.place_list, name="place-list"),
    path("places/new/", editor_views.place_create, name="place-create"),
    path("places/<uuid:place_id>/", editor_views.place_detail, name="place-detail"),
    path("places/<uuid:place_id>/archive/", editor_views.place_archive, name="place-archive"),
    path("places/<uuid:place_id>/reactivate/", editor_views.place_reactivate, name="place-reactivate"),
]
