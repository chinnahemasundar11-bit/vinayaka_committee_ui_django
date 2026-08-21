from django.shortcuts import render
from django.db.models import Sum
from funds.models import FundReceipt
from expenses.models import ExpenseVoucher


def index(request):
    """Financial Reports & Balance Sheet Statement View."""
    total_funds = FundReceipt.objects.aggregate(Sum("amount"))["amount__sum"] or 0
    total_expenses = ExpenseVoucher.objects.aggregate(Sum("amount_spent"))["amount_spent__sum"] or 0
    net_surplus = total_funds - total_expenses

    receipts_by_source = FundReceipt.objects.values("fund_source__name").annotate(total=Sum("amount")).order_by("-total")
    vouchers_by_category = ExpenseVoucher.objects.values("category__name").annotate(total=Sum("amount_spent")).order_by("-total")

    all_receipts = FundReceipt.objects.select_related("fund_source", "payment_method").order_by("-date_received")[:50]
    all_vouchers = ExpenseVoucher.objects.select_related("category", "payment_method").order_by("-expense_date")[:50]

    context = {
        "total_funds": total_funds,
        "total_expenses": total_expenses,
        "net_surplus": net_surplus,
        "receipts_by_source": receipts_by_source,
        "vouchers_by_category": vouchers_by_category,
        "all_receipts": all_receipts,
        "all_vouchers": all_vouchers,
    }
    return render(request, "reports/reports.html", context)
