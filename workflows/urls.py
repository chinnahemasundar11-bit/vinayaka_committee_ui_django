from django.urls import path
from . import views

urlpatterns = [
    path("", views.workflow_list, name="workflow_list"),
    path("email-configs/", views.email_config_list, name="email_config_list"),
    path("my-tasks/", views.my_tasks, name="my_tasks"),
    path("action/", views.task_perform_action, name="task_perform_action"),
]
