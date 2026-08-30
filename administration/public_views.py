from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from funds.models import FundReceipt
from administration.models import SiteSetting, FinancialYear


def get_site_setting(key, default=""):
    obj = SiteSetting.objects.filter(key=key).first()
    return obj.value if obj else default


def wall_of_honor_view(request):
    """
    Unauthenticated Full-Screen LED TV Wall of Honor & Live Donor Ticker Portal.
    Designed for large screens at festival grounds. Auto-refreshes every 15s.
    """
    recent_donors = FundReceipt.objects.select_related("fund_source", "payment_method").order_by("-created_at")[:25]
    top_donors = FundReceipt.objects.order_by("-amount")[:10]
    total_collected = FundReceipt.objects.aggregate(Sum("amount"))["amount__sum"] or 0

    site_name = get_site_setting("SITE_NAME", "Vinayaka Youth Committee")
    site_slogan = get_site_setting("SITE_SLOGAN", "Ganesh Utsav Celebration")
    currency = get_site_setting("CURRENCY_SYMBOL", "₹")

    context = {
        "recent_donors": recent_donors,
        "top_donors": top_donors,
        "total_collected": total_collected,
        "site_name": site_name,
        "site_slogan": site_slogan,
        "currency": currency,
    }
    return render(request, "administration/wall_of_honor.html", context)


def verify_receipt_view(request, receipt_number):
    """
    Unauthenticated Public Donor Self-Verification Portal.
    Allows donors to scan QR codes on printable receipts and verify authenticity.
    """
    receipt = FundReceipt.objects.filter(receipt_number__iexact=receipt_number.strip()).select_related("fund_source", "payment_method").first()
    
    site_name = get_site_setting("SITE_NAME", "Vinayaka Youth Committee")
    currency = get_site_setting("CURRENCY_SYMBOL", "₹")

    context = {
        "receipt": receipt,
        "receipt_number": receipt_number,
        "site_name": site_name,
        "currency": currency,
        "is_valid": receipt is not None and not receipt.is_deleted,
    }
    return render(request, "administration/verify_receipt.html", context)
