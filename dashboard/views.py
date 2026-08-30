from django.shortcuts import render
from django.db.models import Sum, Count
from funds.models import FundReceipt
from expenses.models import ExpenseVoucher
from members.models import Member
from events.models import Event


from accounts.permissions import login_required_custom


@login_required_custom
def index(request):
    """Dynamic financial dashboard view computing aggregations from database models."""
    total_funds = FundReceipt.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_expenses = ExpenseVoucher.objects.aggregate(total=Sum('amount_spent'))['total'] or 0
    net_balance = total_funds - total_expenses
    active_members_count = Member.objects.filter(status='Active').count()
    active_events_count = Event.objects.filter(status='Planned').count()

    try:
        per_page = int(request.GET.get("per_page", 10))
        if per_page not in [10, 50, 100, 500]: per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    from django.core.paginator import Paginator
    receipts_qs = FundReceipt.objects.select_related('fund_source', 'payment_method').order_by('-date_received', '-id')
    expenses_qs = ExpenseVoucher.objects.select_related('category', 'payment_method').order_by('-expense_date', '-id')

    receipts_paginator = Paginator(receipts_qs, per_page)
    receipts_page = receipts_paginator.get_page(request.GET.get("r_page"))

    expenses_paginator = Paginator(expenses_qs, per_page)
    expenses_page = expenses_paginator.get_page(request.GET.get("e_page"))

    context = {
        "total_funds": total_funds,
        "total_expenses": total_expenses,
        "net_balance": net_balance,
        "active_members_count": active_members_count,
        "active_events_count": active_events_count,
        "recent_receipts": receipts_page,
        "recent_expenses": expenses_page,
        "page_obj": receipts_page,
        "per_page": per_page,
    }
    return render(request, "dashboard/dashboard.html", context)
