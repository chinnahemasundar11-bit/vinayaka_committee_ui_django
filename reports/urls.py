from . import views, export_views
from django.urls import path

urlpatterns = [
    path("", views.index, name="index"),
    path("export-csv/", views.export_reports_csv, name="export_reports_csv"),
    path("export/excel/", export_views.export_excel_ledger_view, name="export_excel"),
    path("export/audit-pdf/", export_views.export_audit_pdf_view, name="export_audit_pdf"),
]
