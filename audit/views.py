from django.shortcuts import render
from django.db.models import Q
from .models import AuditLog


def index(request):
    """Audit Trail System Logs View."""
    search_query = request.GET.get("q", "").strip()
    action_filter = request.GET.get("action", "").strip()

    logs_qs = AuditLog.objects.select_related("user").all()

    if search_query:
        logs_qs = logs_qs.filter(
            Q(model_name__icontains=search_query) |
            Q(details__icontains=search_query) |
            Q(user__username__icontains=search_query)
        )

    if action_filter:
        logs_qs = logs_qs.filter(action=action_filter)

    context = {
        "audit_logs": logs_qs,
        "search_query": search_query,
        "action_filter": action_filter,
    }
    return render(request, "audit/audit_logs.html", context)
