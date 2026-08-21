from django.urls import path
from . import views

urlpatterns = [
    path("", views.member_list, name="member_list"),
    path("add/", views.member_add, name="member_add"),
]
