from django.shortcuts import render
from django.db.models import Sum
from funds.models import FundReceipt
from expenses.models import ExpenseVoucher


from accounts.permissions import login_required_custom


@login_required_custom
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


import csv
from django.http import HttpResponse

@login_required_custom
def export_reports_csv(request):
    """Export full financial statement report (Income & Expense Ledger) as CSV."""
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="financial_statement_report.csv"'
    response.write('\ufeff'.encode('utf8'))

    writer = csv.writer(response)
    writer.writerow(["=== VINAYAKA YOUTH COMMITTEE FINANCIAL STATEMENT ==="])
    writer.writerow([])

    total_funds = FundReceipt.objects.aggregate(Sum("amount"))["amount__sum"] or 0
    total_expenses = ExpenseVoucher.objects.aggregate(Sum("amount_spent"))["amount_spent__sum"] or 0
    net_balance = total_funds - total_expenses

    writer.writerow(["SUMMARY OVERVIEW"])
    writer.writerow(["Total Funds Received (INR)", f"{total_funds:.2f}"])
    writer.writerow(["Total Expenses Incurred (INR)", f"{total_expenses:.2f}"])
    writer.writerow(["Net Surplus / Cash Balance (INR)", f"{net_balance:.2f}"])
    writer.writerow([])

    writer.writerow(["INCOME / FUNDS RECEIVED BREAKDOWN"])
    writer.writerow(["Receipt Number", "Donor Name", "Fund Source", "Payment Channel", "Amount (INR)", "Date Received"])
    for r in FundReceipt.objects.select_related("fund_source", "payment_method").order_by("-date_received"):
        writer.writerow([
            r.receipt_number,
            r.donor_name,
            r.fund_source.name if r.fund_source else "",
            r.payment_method.name if r.payment_method else "",
            f"{r.amount:.2f}",
            r.date_received.strftime("%Y-%m-%d") if r.date_received else ""
        ])

    writer.writerow([])
    writer.writerow(["EXPENDITURE REGISTER BREAKDOWN"])
    writer.writerow(["Voucher Number", "Category", "Vendor Name", "Description", "Amount Spent (INR)", "Expense Date", "Status"])
    for v in ExpenseVoucher.objects.select_related("category", "payment_method").order_by("-expense_date"):
        writer.writerow([
            v.voucher_number,
            v.category.name if v.category else "",
            v.vendor_name,
            v.description,
            f"{v.amount_spent:.2f}",
            v.expense_date.strftime("%Y-%m-%d") if v.expense_date else "",
            v.status
        ])

    return response

