from . import views
from django.urls import path

urlpatterns = [
    path("", views.index, name="index"),
    path("users/", views.users, name="users"),
    path("roles/", views.roles, name="roles"),
    path("payment-methods/", views.payment_methods, name="payment_methods"),
    path("fund-sources/", views.fund_sources, name="fund_sources"),
    path("expense-categories/", views.expense_categories, name="expense_categories"),
    path("financial-years/", views.financial_years, name="financial_years"),
    path("site-settings/", views.site_settings, name="site_settings"),
]
