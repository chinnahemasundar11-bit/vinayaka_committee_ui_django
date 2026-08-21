from django.urls import path, include
from django.views.generic import RedirectView
from django.views.i18n import JavaScriptCatalog

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="login", permanent=False)),
    path("i18n/", include("django.conf.urls.i18n")),
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
    path("accounts/", include("accounts.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("funds/", include("funds.urls")),
    path("expenses/", include("expenses.urls")),
    path("reports/", include("reports.urls")),
    path("members/", include("members.urls")),
    path("events/", include("events.urls")),
    path("administration/", include("administration.urls")),
    path("audit/", include("audit.urls")),
]
