from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.utils.translation import gettext as _
from .models import AuditLog
from accounts.permissions import (
    login_required_custom, admin_required, get_user_role, module_access_required
)

from funds.models import FundReceipt
from expenses.models import ExpenseVoucher
from events.models import Event
from members.models import Member
from administration.models import FinancialYear, FundSource, ExpenseCategory, PaymentMethod

MODEL_MAP = {
    "FundReceipt": FundReceipt,
    "ExpenseVoucher": ExpenseVoucher,
    "Event": Event,
    "Member": Member,
    "FinancialYear": FinancialYear,
    "FundSource": FundSource,
    "ExpenseCategory": ExpenseCategory,
    "PaymentMethod": PaymentMethod,
}


@module_access_required("AUDIT_LOGS")
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

    role = get_user_role(request.user)
    can_manage_admin = request.user.is_superuser or role == "Super Admin"

    try:
        per_page = int(request.GET.get("per_page", 10))
        if per_page not in [10, 50, 100, 500]: per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    from django.core.paginator import Paginator
    paginator = Paginator(logs_qs, per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "audit_logs": page_obj,
        "page_obj": page_obj,
        "per_page": per_page,
        "search_query": search_query,
        "action_filter": action_filter,
        "can_manage_admin": can_manage_admin,
    }
    return render(request, "audit/audit_logs.html", context)


@admin_required
def restore_record_view(request, model_name, object_id):
    """1-Click Soft-Delete Recovery View for Super Admins."""
    if request.method != "POST":
        return redirect("/audit/")

    model_cls = MODEL_MAP.get(model_name)
    if not model_cls:
        messages.error(request, _("Restore failed: Unknown model type '%(model)s'.") % {"model": model_name})
        return redirect("/audit/")

    instance = model_cls.all_objects.filter(id=object_id).first()
    if not instance:
        messages.error(request, _("Restore failed: Record '%(model)s' #%(id)s not found.") % {"model": model_name, "id": object_id})
        return redirect("/audit/")

    if not instance.is_deleted:
        messages.info(request, _("Record '%(model)s' #%(id)s is already active.") % {"model": model_name, "id": object_id})
        return redirect("/audit/")

    instance.is_deleted = False
    instance.deleted_at = None
    instance.deleted_by = None
    instance.save()

    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action="RESTORE",
        model_name=model_name,
        object_id=str(object_id),
        details=f"Restored soft-deleted record {model_name} #{object_id}"
    )

    messages.success(request, _("Successfully restored soft-deleted record '%(model)s' #%(id)s!") % {"model": model_name, "id": object_id})
    return redirect("/audit/?action=DELETE")


from .models import NotificationLog

@login_required_custom
def notification_logs_view(request):
    """SMS / WhatsApp Delivery Log & Notification Dispatch Audit Tracker."""
    channel_filter = request.GET.get("channel", "").strip()
    search_query = request.GET.get("q", "").strip()

    logs_qs = NotificationLog.objects.select_related("triggered_by").all()

    if channel_filter:
        logs_qs = logs_qs.filter(channel=channel_filter)

    if search_query:
        logs_qs = logs_qs.filter(
            Q(recipient_name__icontains=search_query) |
            Q(recipient_phone__icontains=search_query) |
            Q(purpose__icontains=search_query) |
            Q(message_body__icontains=search_query)
        )

    total_count = NotificationLog.objects.count()
    whatsapp_count = NotificationLog.objects.filter(channel="WHATSAPP").count()
    sms_count = NotificationLog.objects.filter(channel="SMS").count()
    otp_count = NotificationLog.objects.filter(channel="OTP").count()

    try:
        per_page = int(request.GET.get("per_page", 10))
        if per_page not in [10, 50, 100, 500]: per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    from django.core.paginator import Paginator
    paginator = Paginator(logs_qs, per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "notification_logs": page_obj,
        "page_obj": page_obj,
        "per_page": per_page,
        "channel_filter": channel_filter,
        "search_query": search_query,
        "total_count": total_count,
        "whatsapp_count": whatsapp_count,
        "sms_count": sms_count,
        "otp_count": otp_count,
    }
    return render(request, "audit/notification_logs.html", context)

