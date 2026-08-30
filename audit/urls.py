from . import views
from django.urls import path

urlpatterns = [
    path("", views.index, name="index"),
    path("notifications/", views.notification_logs_view, name="notification_logs"),
    path("restore/<str:model_name>/<int:object_id>/", views.restore_record_view, name="restore_record"),
]
