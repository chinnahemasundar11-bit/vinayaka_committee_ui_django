from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Q
from .models import FundReceipt
from administration.models import FundSource, PaymentMethod
from audit.models import AuditLog
import datetime


def fund_list(request):
    """List, search, create, update, and delete fund receipts."""
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create":
            receipt_no = request.POST.get("receipt_number", "").strip() or f"RCPT-2026-{FundReceipt.objects.count() + 1:03d}"
            donor_name = request.POST.get("donor_name", "").strip()
            donor_phone = request.POST.get("donor_phone", "").strip()
            source_id = request.POST.get("fund_source")
            method_id = request.POST.get("payment_method")
            amount = request.POST.get("amount", 0)
            date_received = request.POST.get("date_received") or datetime.date.today().isoformat()
            ref_no = request.POST.get("reference_number", "").strip()
            remarks = request.POST.get("remarks", "").strip()

            if donor_name and source_id and method_id and amount:
                source = get_object_or_404(FundSource, id=source_id)
                method = get_object_or_404(PaymentMethod, id=method_id)

                receipt = FundReceipt.objects.create(
                    receipt_number=receipt_no,
                    donor_name=donor_name,
                    donor_phone=donor_phone,
                    fund_source=source,
                    payment_method=method,
                    amount=amount,
                    date_received=date_received,
                    reference_number=ref_no,
                    remarks=remarks
                )
                user = request.user if request.user.is_authenticated else None
                AuditLog.objects.create(user=user, action="CREATE", model_name="FundReceipt", object_id=str(receipt.id), details=f"Created receipt {receipt_no} for {donor_name} (₹{amount})")
                messages.success(request, f"Fund receipt {receipt_no} recorded successfully!")
            else:
                messages.error(request, "* Please fill all mandatory fields.")

        elif action == "update":
            receipt_id = request.POST.get("receipt_id")
            receipt = get_object_or_404(FundReceipt, id=receipt_id)
            receipt.donor_name = request.POST.get("donor_name", receipt.donor_name)
            receipt.donor_phone = request.POST.get("donor_phone", receipt.donor_phone)
            source_id = request.POST.get("fund_source")
            method_id = request.POST.get("payment_method")
            if source_id: receipt.fund_source_id = source_id
            if method_id: receipt.payment_method_id = method_id
            receipt.amount = request.POST.get("amount", receipt.amount)
            receipt.date_received = request.POST.get("date_received", receipt.date_received)
            receipt.save()

            user = request.user if request.user.is_authenticated else None
            AuditLog.objects.create(user=user, action="UPDATE", model_name="FundReceipt", object_id=str(receipt.id), details=f"Updated receipt {receipt.receipt_number}")
            messages.success(request, f"Fund receipt {receipt.receipt_number} updated successfully!")

        elif action == "delete":
            receipt_id = request.POST.get("receipt_id")
            receipt = get_object_or_404(FundReceipt, id=receipt_id)
            receipt_no = receipt.receipt_number
            receipt.delete()
            user = request.user if request.user.is_authenticated else None
            AuditLog.objects.create(user=user, action="DELETE", model_name="FundReceipt", object_id=str(receipt_id), details=f"Deleted receipt {receipt_no}")
            messages.success(request, f"Fund receipt {receipt_no} deleted successfully.")

        elif action == "bulk_delete":
            selected_ids = request.POST.getlist("selected_ids[]") or request.POST.getlist("selected_ids")
            if selected_ids:
                receipts = FundReceipt.objects.filter(id__in=selected_ids)
                count = receipts.count()
                for r in receipts:
                    r.delete()
                user = request.user if request.user.is_authenticated else None
                AuditLog.objects.create(user=user, action="BULK_DELETE", model_name="FundReceipt", object_id=str(selected_ids), details=f"Bulk deleted {count} receipts")
                messages.success(request, f"Successfully deleted {count} selected receipts.")

        return redirect("/funds/")

    search_query = request.GET.get("q", "").strip()
    receipts_qs = FundReceipt.objects.select_related("fund_source", "payment_method")
    if search_query:
        receipts_qs = receipts_qs.filter(
            Q(receipt_number__icontains=search_query) |
            Q(donor_name__icontains=search_query) |
            Q(donor_phone__icontains=search_query)
        )

    fund_sources = FundSource.objects.filter(is_active=True)
    payment_methods = PaymentMethod.objects.filter(is_active=True)
    total_collected = receipts_qs.aggregate(Sum("amount"))["amount__sum"] or 0

    context = {
        "receipts": receipts_qs,
        "fund_sources": fund_sources,
        "payment_methods": payment_methods,
        "total_collected": total_collected,
        "search_query": search_query,
    }
    return render(request, "funds/fund_list.html", context)


def fund_add(request):
    """Dedicated Add Fund Receipt View."""
    if request.method == "POST":
        return fund_list(request)

    fund_sources = FundSource.objects.filter(is_active=True)
    payment_methods = PaymentMethod.objects.filter(is_active=True)
    next_receipt_no = f"RCPT-2026-{FundReceipt.objects.count() + 1:03d}"
    today_date = datetime.date.today().isoformat()

    context = {
        "fund_sources": fund_sources,
        "payment_methods": payment_methods,
        "next_receipt_no": next_receipt_no,
        "today_date": today_date,
    }
    return render(request, "funds/fund_form.html", context)
