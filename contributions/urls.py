from django.urls import path

from . import views

app_name = "contributions"

urlpatterns = [path("api/contributions/", views.submit_contribution, name="submit")]
