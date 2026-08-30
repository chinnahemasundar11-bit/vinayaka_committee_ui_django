from django.urls import path
from . import views

urlpatterns = [
    path("", views.fund_list, name="fund_list"),
    path("add/", views.fund_add, name="fund_add"),
    path("<int:receipt_id>/print/", views.fund_receipt_print, name="fund_receipt_print"),
    path("export-csv/", views.export_funds_csv, name="export_funds_csv"),
    path("api/sync-offline-receipts/", views.sync_offline_receipts, name="sync_offline_receipts"),
]
