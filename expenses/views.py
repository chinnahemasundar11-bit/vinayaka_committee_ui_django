from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Q
from .models import ExpenseVoucher
from administration.models import ExpenseCategory, PaymentMethod
from audit.models import AuditLog
import datetime


def expense_list(request):
    """List, search, create, update, and delete expense vouchers."""
    if request.method == "POST":
        action = request.POST.get("action")

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
                    status="Approved"
                )
                user = request.user if request.user.is_authenticated else None
                AuditLog.objects.create(user=user, action="CREATE", model_name="ExpenseVoucher", object_id=str(voucher.id), details=f"Created expense voucher {voucher_no} to {vendor_name} (₹{amount_spent})")
                messages.success(request, f"Expense voucher {voucher_no} recorded successfully!")
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

    context = {
        "vouchers": vouchers_qs,
        "categories": expense_categories,
        "payment_methods": payment_methods,
        "total_spent": total_spent,
        "search_query": search_query,
    }
    return render(request, "expenses/expense_list.html", context)


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
