from django.urls import path
from . import views

urlpatterns = [
    path("", views.member_list, name="member_list"),
    path("add/", views.member_add, name="member_add"),
    path("export-csv/", views.export_members_csv, name="export_members_csv"),
]
