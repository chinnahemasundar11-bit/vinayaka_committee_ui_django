from django.urls import path, include
from django.views.generic import RedirectView
from django.views.i18n import JavaScriptCatalog
from django.conf import settings
from django.conf.urls.static import static
from administration.public_views import wall_of_honor_view, verify_receipt_view

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="login", permanent=False)),
    path("i18n/", include("django.conf.urls.i18n")),
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
    path("public/wall-of-honor/", wall_of_honor_view, name="wall_of_honor"),
    path("public/verify-receipt/<str:receipt_number>/", verify_receipt_view, name="verify_receipt"),
    path("accounts/", include("accounts.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("funds/", include("funds.urls")),
    path("expenses/", include("expenses.urls")),
    path("reports/", include("reports.urls")),
    path("members/", include("members.urls")),
    path("events/", include("events.urls")),
    path("administration/", include("administration.urls")),
    path("audit/", include("audit.urls")),
    path("workflows/", include("workflows.urls")),
    path("qa-dashboard/", include("qa_dashboard.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
