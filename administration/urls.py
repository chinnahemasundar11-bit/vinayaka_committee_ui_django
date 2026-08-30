from . import views, public_views, analytics_views, backup_views
from django.urls import path

urlpatterns = [
    path("", views.index, name="index"),
    path("users/", views.users, name="users"),
    path("modules/", views.modules, name="modules"),
    path("roles/", views.roles, name="roles"),
    path("payment-methods/", views.payment_methods, name="payment_methods"),
    path("fund-sources/", views.fund_sources, name="fund_sources"),
    path("expense-categories/", views.expense_categories, name="expense_categories"),
    path("financial-years/", views.financial_years, name="financial_years"),
    path("switch-year/<int:year_id>/", views.switch_year_view, name="switch_year"),
    path("site-settings/", views.site_settings, name="site_settings"),
    path("analytics/expense-predictor/", analytics_views.expense_predictor_view, name="expense_predictor"),
    path("backups/", backup_views.backup_vault_view, name="backup_vault"),
    path("backups/download/<str:filename>/", backup_views.download_backup_view, name="download_backup"),
]
