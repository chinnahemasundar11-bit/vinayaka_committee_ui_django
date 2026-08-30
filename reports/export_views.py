import csv
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.db.models import Sum
from funds.models import FundReceipt
from expenses.models import ExpenseVoucher
from administration.models import SiteSetting, FinancialYear
from accounts.permissions import login_required_custom


def get_site_setting(key, default=""):
    obj = SiteSetting.objects.filter(key=key).first()
    return obj.value if obj else default


@login_required_custom
def export_excel_ledger_view(request):
    """
    Generates dynamic Financial Audit Ledger Spreadsheet (.xlsx / .csv)
    containing itemized fund receipts, vendor expenses, and net summary.
    """
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Festival Financial Ledger"

        site_name = get_site_setting("SITE_NAME", "Vinayaka Youth Committee")
        currency = get_site_setting("CURRENCY_SYMBOL", "₹")

        # Styling definitions
        header_fill = PatternFill(start_color="8B1E24", end_color="8B1E24", fill_type="solid")
        header_font = Font(name="Calibri", size=12, bold=True, color="FFFFFF")
        title_font = Font(name="Calibri", size=16, bold=True, color="8B1E24")
        bold_font = Font(name="Calibri", size=11, bold=True)

        # Title Block
        ws.merge_cells("A1:F1")
        ws["A1"] = f"{site_name} - Official Financial Ledger Statement"
        ws["A1"].font = title_font
        ws["A1"].alignment = Alignment(horizontal="center")

        ws.append([]) # Empty row

        # Fund Receipts Section
        ws.append(["FUND CONTRIBUTIONS & DONATIONS RECEIPT LEDGER"])
        ws["A3"].font = bold_font

        headers_receipts = ["Receipt #", "Date", "Donor Name", "Mobile", "Category", f"Amount ({currency})"]
        ws.append(headers_receipts)
        for col_num in range(1, 7):
            cell = ws.cell(row=4, column=col_num)
            cell.fill = header_fill
            cell.font = header_font

        receipts = FundReceipt.objects.select_related("fund_source").order_by("-date_received")
        total_receipts = 0
        for r in receipts:
            ws.append([r.receipt_number, r.date_received.strftime("%Y-%m-%d") if r.date_received else "", r.donor_name, r.donor_phone, r.fund_source.name, float(r.amount)])
            total_receipts += float(r.amount)

        ws.append(["TOTAL COLLECTIONS", "", "", "", "", total_receipts])
        ws.cell(row=ws.max_row, column=1).font = bold_font
        ws.cell(row=ws.max_row, column=6).font = bold_font

        ws.append([]) # Empty row

        # Expense Vouchers Section
        ws.append(["VENDOR EXPENSES & APPROVED VOUCHERS LEDGER"])
        ws.cell(row=ws.max_row, column=1).font = bold_font

        headers_expenses = ["Voucher #", "Date", "Vendor Name", "Category", "Status", f"Amount Spent ({currency})"]
        ws.append(headers_expenses)
        exp_header_row = ws.max_row
        for col_num in range(1, 7):
            cell = ws.cell(row=exp_header_row, column=col_num)
            cell.fill = header_fill
            cell.font = header_font

        expenses = ExpenseVoucher.objects.select_related("category").order_by("-expense_date")
        total_expenses = 0
        for e in expenses:
            ws.append([e.voucher_number, e.expense_date.strftime("%Y-%m-%d") if e.expense_date else "", e.vendor_name, e.category.name, e.status, float(e.amount_spent)])
            if e.status == "APPROVED":
                total_expenses += float(e.amount_spent)

        ws.append(["TOTAL APPROVED EXPENSES", "", "", "", "", total_expenses])
        ws.cell(row=ws.max_row, column=1).font = bold_font
        ws.cell(row=ws.max_row, column=6).font = bold_font

        # Adjust Column Widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 14)

        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = 'attachment; filename="Festival_Financial_Ledger.xlsx"'
        wb.save(response)
        return response

    except ImportError:
        # Fallback to standard CSV output if openpyxl is not installed
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="Festival_Financial_Ledger.csv"'
        writer = csv.writer(response)
        writer.writerow(["Type", "Number", "Date", "Name/Vendor", "Category", "Amount"])
        
        for r in FundReceipt.objects.all():
            writer.writerow(["INCOME", r.receipt_number, r.date_received, r.donor_name, r.fund_source.name, r.amount])
        for e in ExpenseVoucher.objects.all():
            writer.writerow(["EXPENSE", e.voucher_number, e.expense_date, e.vendor_name, e.category.name, e.amount_spent])
        
        return response


@login_required_custom
def export_audit_pdf_view(request):
    """
    Renders printable Executive Committee Meeting Audit PDF Statement.
    """
    receipts = FundReceipt.objects.select_related("fund_source").order_by("-date_received")[:50]
    expenses = ExpenseVoucher.objects.select_related("category").order_by("-expense_date")[:50]

    total_income = float(FundReceipt.objects.aggregate(Sum("amount"))["amount__sum"] or 0)
    total_expenses = float(ExpenseVoucher.objects.filter(status="APPROVED").aggregate(Sum("amount_spent"))["amount_spent__sum"] or 0)
    net_closing_balance = total_income - total_expenses

    site_name = get_site_setting("SITE_NAME", "Vinayaka Youth Committee")
    currency = get_site_setting("CURRENCY_SYMBOL", "₹")

    context = {
        "receipts": receipts,
        "expenses": expenses,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_closing_balance": net_closing_balance,
        "site_name": site_name,
        "currency": currency,
    }
    return render(request, "reports/audit_statement.html", context)
