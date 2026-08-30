from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Q
from .models import ExpenseVoucher
from administration.models import ExpenseCategory, PaymentMethod
from audit.models import AuditLog
import datetime


from accounts.permissions import login_required_custom, get_user_role, has_module_action_right, treasurer_required


@login_required_custom
def expense_list(request):
    """List, search, create, update, and delete expense vouchers."""
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create" and not has_module_action_right(request.user, "EXPENSES", "add"):
            messages.error(request, "Access Denied: You do not have permission to add expense vouchers.")
            return redirect("/expenses/")
        elif action in ["update", "edit"] and not has_module_action_right(request.user, "EXPENSES", "edit"):
            messages.error(request, "Access Denied: You do not have permission to edit expense vouchers.")
            return redirect("/expenses/")
        elif action == "delete" and not has_module_action_right(request.user, "EXPENSES", "delete_single"):
            messages.error(request, "Access Denied: You do not have permission to delete expense vouchers.")
            return redirect("/expenses/")
        elif action == "bulk_delete" and not has_module_action_right(request.user, "EXPENSES", "delete_bulk"):
            messages.error(request, "Access Denied: You do not have permission to bulk delete expense vouchers.")
            return redirect("/expenses/")


        if action == "create":
            voucher_no = request.POST.get("voucher_number", "").strip() or f"EXP-2026-{ExpenseVoucher.objects.count() + 1:03d}"
            cat_id = request.POST.get("category")
            vendor_name = request.POST.get("vendor_name", "").strip()
            amount_spent = request.POST.get("amount_spent", 0)
            expense_date = request.POST.get("expense_date") or datetime.date.today().isoformat()
            method_id = request.POST.get("payment_method")
            description = request.POST.get("description", "").strip()

            if cat_id and vendor_name and amount_spent and method_id and description:
                category = get_object_or_404(ExpenseCategory, id=cat_id)
                method = get_object_or_404(PaymentMethod, id=method_id)

                voucher = ExpenseVoucher.objects.create(
                    voucher_number=voucher_no,
                    category=category,
                    vendor_name=vendor_name,
                    amount_spent=amount_spent,
                    expense_date=expense_date,
                    payment_method=method,
                    description=description,
                    status="Pending Approval" if category.requires_approval else "Approved"
                )
                user = request.user if request.user.is_authenticated else None
                AuditLog.objects.create(user=user, action="CREATE", model_name="ExpenseVoucher", object_id=str(voucher.id), details=f"Created expense voucher {voucher_no} to {vendor_name} (₹{amount_spent})")

                # Initiate Enterprise Workflow
                from workflows.services import start_workflow_for_object
                try:
                    start_workflow_for_object(
                        module_code="EXPENSE",
                        object_id=voucher_no,
                        submitter=user,
                        amount=float(amount_spent)
                    )
                except Exception:
                    pass

                messages.success(request, f"Expense voucher {voucher_no} recorded and initiated into approval workflow!")
            else:
                messages.error(request, "* Please fill all mandatory fields.")

        elif action == "update":
            voucher_id = request.POST.get("voucher_id")
            voucher = get_object_or_404(ExpenseVoucher, id=voucher_id)
            voucher.vendor_name = request.POST.get("vendor_name", voucher.vendor_name)
            cat_id = request.POST.get("category")
            method_id = request.POST.get("payment_method")
            if cat_id: voucher.category_id = cat_id
            if method_id: voucher.payment_method_id = method_id
            voucher.amount_spent = request.POST.get("amount_spent", voucher.amount_spent)
            voucher.expense_date = request.POST.get("expense_date", voucher.expense_date)
            voucher.description = request.POST.get("description", voucher.description)
            voucher.save()

            user = request.user if request.user.is_authenticated else None
            AuditLog.objects.create(user=user, action="UPDATE", model_name="ExpenseVoucher", object_id=str(voucher.id), details=f"Updated expense voucher {voucher.voucher_number}")
            messages.success(request, f"Expense voucher {voucher.voucher_number} updated successfully!")

        elif action == "delete":
            voucher_id = request.POST.get("voucher_id")
            voucher = get_object_or_404(ExpenseVoucher, id=voucher_id)
            v_no = voucher.voucher_number
            voucher.delete()
            user = request.user if request.user.is_authenticated else None
            AuditLog.objects.create(user=user, action="DELETE", model_name="ExpenseVoucher", object_id=str(voucher_id), details=f"Deleted expense voucher {v_no}")
            messages.success(request, f"Expense voucher {v_no} deleted successfully.")

        elif action == "bulk_delete":
            selected_ids = request.POST.getlist("selected_ids[]") or request.POST.getlist("selected_ids")
            if selected_ids:
                vouchers = ExpenseVoucher.objects.filter(id__in=selected_ids)
                count = vouchers.count()
                for v in vouchers:
                    v.delete()
                user = request.user if request.user.is_authenticated else None
                AuditLog.objects.create(user=user, action="BULK_DELETE", model_name="ExpenseVoucher", object_id=str(selected_ids), details=f"Bulk deleted {count} expense vouchers")
                messages.success(request, f"Successfully deleted {count} selected expense vouchers.")

        return redirect("/expenses/")

    search_query = request.GET.get("q", "").strip()
    vouchers_qs = ExpenseVoucher.objects.select_related("category", "payment_method")
    if search_query:
        vouchers_qs = vouchers_qs.filter(
            Q(voucher_number__icontains=search_query) |
            Q(vendor_name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    expense_categories = ExpenseCategory.objects.filter(is_active=True)
    payment_methods = PaymentMethod.objects.filter(is_active=True)
    total_spent = vouchers_qs.aggregate(Sum("amount_spent"))["amount_spent__sum"] or 0

    try:
        per_page = int(request.GET.get("per_page", 10))
        if per_page not in [10, 50, 100, 500]: per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    from django.core.paginator import Paginator
    paginator = Paginator(vouchers_qs, per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "vouchers": page_obj,
        "page_obj": page_obj,
        "per_page": per_page,
        "categories": expense_categories,
        "payment_methods": payment_methods,
        "total_spent": total_spent,
        "search_query": search_query,
    }
    return render(request, "expenses/expense_list.html", context)


@treasurer_required
def expense_add(request):
    """Dedicated Add Expense Voucher View."""
    if request.method == "POST":
        return expense_list(request)

    expense_categories = ExpenseCategory.objects.filter(is_active=True)
    payment_methods = PaymentMethod.objects.filter(is_active=True)
    next_voucher_no = f"EXP-2026-{ExpenseVoucher.objects.count() + 1:03d}"
    today_date = datetime.date.today().isoformat()

    context = {
        "categories": expense_categories,
        "payment_methods": payment_methods,
        "next_voucher_no": next_voucher_no,
        "today_date": today_date,
    }
    return render(request, "expenses/expense_form.html", context)


import csv
from django.http import HttpResponse

@login_required_custom
def export_expenses_csv(request):
    """Export filtered or full expense register as downloadable CSV file."""
    search_query = request.GET.get("q", "").strip()
    vouchers_qs = ExpenseVoucher.objects.select_related("category", "payment_method")
    if search_query:
        vouchers_qs = vouchers_qs.filter(
            Q(voucher_number__icontains=search_query) |
            Q(vendor_name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="expense_register.csv"'
    response.write('\ufeff'.encode('utf8'))

    writer = csv.writer(response)
    writer.writerow(["Voucher Number", "Category", "Vendor Name", "Description", "Amount Spent (INR)", "Expense Date", "Payment Channel", "Status"])

    for v in vouchers_qs:
        writer.writerow([
            v.voucher_number,
            v.category.name if v.category else "",
            v.vendor_name,
            v.description,
            f"{v.amount_spent:.2f}",
            v.expense_date.strftime("%Y-%m-%d") if v.expense_date else "",
            v.payment_method.name if v.payment_method else "",
            v.status
        ])

    return response

