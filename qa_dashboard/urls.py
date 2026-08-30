from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="test_dashboard"),
    path("api/metrics/", views.api_metrics, name="api_metrics"),
    path("api/run-tests/", views.api_run_tests, name="api_run_tests"),
]
