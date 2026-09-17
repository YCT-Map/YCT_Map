from django.urls import path

from . import views

app_name = "routing"
urlpatterns = [path("api/debug/walkable-network/", views.demo_network, name="demo-network")]
