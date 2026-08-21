from django.shortcuts import render
from django.db.models import Sum, Count
from funds.models import FundReceipt
from expenses.models import ExpenseVoucher
from members.models import Member
from events.models import Event


def index(request):
    """Dynamic financial dashboard view computing aggregations from database models."""
    total_funds = FundReceipt.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_expenses = ExpenseVoucher.objects.aggregate(total=Sum('amount_spent'))['total'] or 0
    net_balance = total_funds - total_expenses
    active_members_count = Member.objects.filter(status='Active').count()
    active_events_count = Event.objects.filter(status='Planned').count()

    recent_receipts = FundReceipt.objects.select_related('fund_source', 'payment_method').order_by('-date_received', '-id')[:5]
    recent_expenses = ExpenseVoucher.objects.select_related('category', 'payment_method').order_by('-expense_date', '-id')[:5]

    context = {
        "total_funds": total_funds,
        "total_expenses": total_expenses,
        "net_balance": net_balance,
        "active_members_count": active_members_count,
        "active_events_count": active_events_count,
        "recent_receipts": recent_receipts,
        "recent_expenses": recent_expenses,
    }
    return render(request, "dashboard/dashboard.html", context)
