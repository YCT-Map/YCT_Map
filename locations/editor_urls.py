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
    path("places/<uuid:place_id>/entrances/new/", editor_views.entrance_create, name="entrance-create"),
    path("places/<uuid:place_id>/entrances/<uuid:entrance_id>/", editor_views.entrance_edit, name="entrance-edit"),
    path("places/<uuid:place_id>/floors/new/", editor_views.floor_create, name="floor-create"),
    path("places/<uuid:place_id>/floors/<uuid:floor_id>/", editor_views.floor_edit, name="floor-edit"),
    path("places/<uuid:place_id>/inside/new/", editor_views.internal_create, name="internal-create"),
    path("places/<uuid:place_id>/inside/<uuid:internal_id>/", editor_views.internal_edit, name="internal-edit"),
    path("contributions/", editor_views.contribution_list, name="contribution-list"),
    path("contributions/<uuid:contribution_id>/", editor_views.contribution_detail, name="contribution-detail"),
    path("paths/", editor_views.path_list, name="path-list"),
    path("paths/nodes/new/", editor_views.node_create, name="node-create"),
    path("paths/nodes/<uuid:node_id>/", editor_views.node_edit, name="node-edit"),
    path("paths/segments/new/", editor_views.segment_create, name="segment-create"),
    path("paths/segments/<uuid:segment_id>/", editor_views.segment_edit, name="segment-edit"),
    path("paths/segments/<uuid:segment_id>/split/", editor_views.segment_split, name="segment-split"),
]
