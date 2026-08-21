from django.urls import path
from . import views

urlpatterns = [
    path("", views.fund_list, name="fund_list"),
    path("add/", views.fund_add, name="fund_add"),
]
