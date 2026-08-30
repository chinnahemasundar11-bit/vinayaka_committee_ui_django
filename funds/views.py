from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Q
from .models import FundReceipt
from administration.models import FundSource, PaymentMethod
from audit.models import AuditLog
import datetime


from accounts.permissions import login_required_custom, get_user_role, has_module_action_right, treasurer_required


@login_required_custom
def fund_list(request):
    """List, search, create, update, and delete fund receipts."""
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create" and not has_module_action_right(request.user, "FUNDS_RECEIVED", "add"):
            messages.error(request, "Access Denied: You do not have permission to add fund receipts.")
            return redirect("/funds/")
        elif action in ["update", "edit"] and not has_module_action_right(request.user, "FUNDS_RECEIVED", "edit"):
            messages.error(request, "Access Denied: You do not have permission to edit fund receipts.")
            return redirect("/funds/")
        elif action == "delete" and not has_module_action_right(request.user, "FUNDS_RECEIVED", "delete_single"):
            messages.error(request, "Access Denied: You do not have permission to delete fund receipts.")
            return redirect("/funds/")
        elif action == "bulk_delete" and not has_module_action_right(request.user, "FUNDS_RECEIVED", "delete_bulk"):
            messages.error(request, "Access Denied: You do not have permission to bulk delete fund receipts.")
            return redirect("/funds/")


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

    try:
        per_page = int(request.GET.get("per_page", 10))
        if per_page not in [10, 50, 100, 500]: per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    from django.core.paginator import Paginator
    paginator = Paginator(receipts_qs, per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    from .services import build_whatsapp_receipt_url
    for r in page_obj:
        r.whatsapp_url = build_whatsapp_receipt_url(r, request.user)

    context = {
        "receipts": page_obj,
        "page_obj": page_obj,
        "per_page": per_page,
        "fund_sources": fund_sources,
        "payment_methods": payment_methods,
        "total_collected": total_collected,
        "search_query": search_query,
    }
    return render(request, "funds/fund_list.html", context)


@treasurer_required
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


import csv
from django.http import HttpResponse
from administration.utils import amount_to_words

@login_required_custom
def fund_receipt_print(request, receipt_id):
    """Render printable receipt view with amount in words and WhatsApp URL."""
    from .services import build_whatsapp_receipt_url
    receipt = get_object_or_404(FundReceipt.objects.select_related("fund_source", "payment_method"), id=receipt_id)
    amount_in_words = amount_to_words(receipt.amount)
    whatsapp_url = build_whatsapp_receipt_url(receipt, request.user)
    context = {
        "receipt": receipt,
        "amount_in_words": amount_in_words,
        "whatsapp_url": whatsapp_url,
    }
    return render(request, "funds/receipt_print.html", context)


@login_required_custom
def export_funds_csv(request):
    """Export filtered or full fund receipts register as downloadable CSV file."""
    search_query = request.GET.get("q", "").strip()
    receipts_qs = FundReceipt.objects.select_related("fund_source", "payment_method")
    if search_query:
        receipts_qs = receipts_qs.filter(
            Q(receipt_number__icontains=search_query) |
            Q(donor_name__icontains=search_query) |
            Q(donor_phone__icontains=search_query)
        )

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="funds_received_register.csv"'
    response.write('\ufeff'.encode('utf8')) # UTF-8 BOM for Excel

    writer = csv.writer(response)
    writer.writerow(["Receipt Number", "Donor Name", "Donor Phone", "Fund Source", "Payment Channel", "Amount (INR)", "Date Received", "Reference No", "Remarks"])

    for r in receipts_qs:
        writer.writerow([
            r.receipt_number,
            r.donor_name,
            r.donor_phone,
            r.fund_source.name if r.fund_source else "",
            r.payment_method.name if r.payment_method else "",
            f"{r.amount:.2f}",
            r.date_received.strftime("%Y-%m-%d") if r.date_received else "",
            r.reference_number,
            r.remarks
        ])

    return response


import json
from django.http import JsonResponse

@login_required_custom
def sync_offline_receipts(request):
    """Bulk API endpoint to ingest queued offline mobile receipts."""
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        receipts_list = data.get("receipts", [])
        synced_count = 0

        default_fs = FundSource.objects.filter(is_active=True).first()
        default_pm = PaymentMethod.objects.filter(is_active=True).first()

        for item in receipts_list:
            donor_name = item.get("donor_name", "").strip()
            amount_val = float(item.get("amount", 0) or 0)
            if not donor_name or amount_val <= 0:
                continue

            rcpt_no = item.get("receipt_number") or f"RCPT-OFFLINE-{FundReceipt.objects.count() + 1:04d}"
            fs_id = item.get("fund_source")
            pm_id = item.get("payment_method")

            fs_obj = FundSource.objects.filter(id=fs_id).first() if fs_id else default_fs
            pm_obj = PaymentMethod.objects.filter(id=pm_id).first() if pm_id else default_pm

            rec = FundReceipt.objects.create(
                receipt_number=rcpt_no,
                donor_name=donor_name,
                donor_phone=item.get("donor_phone", ""),
                fund_source=fs_obj,
                payment_method=pm_obj,
                amount=amount_val,
                date_received=item.get("date_received") or datetime.date.today(),
                reference_number=item.get("reference_number", "OFFLINE-SYNC"),
                remarks=item.get("remarks", "Offline PWA Mobile Receipt")
            )
            AuditLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action="CREATE",
                model_name="FundReceipt",
                object_id=str(rec.id),
                details=f"Synced offline cash receipt {rcpt_no} for {donor_name} (₹{amount_val})"
            )
            synced_count += 1

        return JsonResponse({"status": "success", "synced_count": synced_count})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


