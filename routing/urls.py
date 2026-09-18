from django.urls import path

from . import views

app_name = "routing"
urlpatterns = [
    path("api/routes/", views.public_route, name="public-route"),
    path("api/debug/walkable-network/", views.demo_network, name="demo-network"),
    path("api/debug/route-anchors/", views.demo_route_anchors, name="demo-route-anchors"),
    path("api/debug/route/", views.demo_route, name="demo-route"),
]
