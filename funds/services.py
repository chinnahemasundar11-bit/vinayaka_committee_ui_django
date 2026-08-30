import re
import urllib.parse
from django.conf import settings
from administration.models import SiteSetting
from audit.models import AuditLog


def get_site_setting(key, default=""):
    """Retrieve site setting value by key."""
    obj = SiteSetting.objects.filter(key=key).first()
    return obj.value if obj else default


def format_phone_for_whatsapp(phone_str):
    """Clean phone number string and add Indian country code 91 if 10-digit number."""
    if not phone_str:
        return ""
    digits = re.sub(r"\D", "", str(phone_str))
    if len(digits) == 10:
        return f"91{digits}"
    return digits


def build_whatsapp_receipt_url(receipt, user=None):
    """
    Generates a pre-filled 1-Click WhatsApp API deep link for donor receipts.
    Format: https://api.whatsapp.com/send?phone=...&text=...
    """
    phone = format_phone_for_whatsapp(receipt.donor_phone)
    site_name = get_site_setting("SITE_NAME", "Vinayaka Youth Committee")
    currency = get_site_setting("CURRENCY_SYMBOL", "₹")

    date_str = receipt.date_received.strftime("%d %b %Y") if receipt.date_received else ""
    source_name = receipt.fund_source.name if receipt.fund_source else "Festival Fund"
    method_name = receipt.payment_method.name if receipt.payment_method else "Cash"

    message_text = (
        f"🚩 *{site_name.upper()}* 🚩\n"
        f"*OFFICIAL DONATION RECEIPT ACKNOWLEDGMENT*\n\n"
        f"Dear *{receipt.donor_name}*,\n\n"
        f"Thank you for your generous contribution of *{currency} {receipt.amount:.2f}* towards *{site_name}*.\n\n"
        f"📋 *Receipt Details:*\n"
        f"• *Receipt No:* {receipt.receipt_number}\n"
        f"• *Date:* {date_str}\n"
        f"• *Fund Category:* {source_name}\n"
        f"• *Payment Mode:* {method_name}\n\n"
        f"May Lord Ganesha bless you and your family with health, peace, and prosperity! 🙏✨\n\n"
        f"Regards,\n"
        f"*{site_name} Management*"
    )

    encoded_text = urllib.parse.quote(message_text)
    if phone:
        whatsapp_url = f"https://api.whatsapp.com/send?phone={phone}&text={encoded_text}"
    else:
        whatsapp_url = f"https://api.whatsapp.com/send?text={encoded_text}"

    try:
        print(f"\n==========================================")
        print(f" [FREE WHATSAPP DISPATCH] Donor: {receipt.donor_name} | Phone: {phone}")
        print(f" URL: {whatsapp_url}")
        print(f"==========================================\n")
    except UnicodeEncodeError:
        pass

    # Log into NotificationLog audit trail
    from audit.notifications import log_notification
    log_notification(
        recipient_phone=receipt.donor_phone or phone or "N/A",
        recipient_name=receipt.donor_name,
        channel="WHATSAPP",
        purpose="DONATION_RECEIPT",
        message_body=message_text,
        dispatch_url=whatsapp_url,
        status="SENT",
        user=user
    )

    return whatsapp_url


def send_sms_receipt_notification(receipt, user=None):
    """
    Dispatches SMS notification payload via live SMS gateway API (Fast2SMS/Twilio) if SMS_API_KEY is configured,
    otherwise logs payload for free testing.
    """
    site_name = get_site_setting("SITE_NAME", "Vinayaka Committee")
    currency = get_site_setting("CURRENCY_SYMBOL", "INR")

    sms_text = f"Received {currency} {receipt.amount:.2f} from {receipt.donor_name} for {site_name}. Receipt No: {receipt.receipt_number}. Thank you! - Vinayaka Team"
    
    api_key = getattr(settings, "SMS_API_KEY", "")
    phone = format_phone_for_whatsapp(receipt.donor_phone)
    status = "SENT"
    dispatch_url = getattr(settings, "SMS_GATEWAY_URL", "")

    if api_key and phone:
        try:
            import json, urllib.request
            route = getattr(settings, "SMS_ROUTE", "q")
            clean_number = phone[-10:] if len(phone) >= 10 else phone
            
            sms_payload = {
                "route": route,
                "message": sms_text,
                "language": "english",
                "numbers": clean_number
            }
            if route == "dlt":
                sms_payload["sender_id"] = getattr(settings, "SMS_SENDER_ID", "VINYKA")

            payload_bytes = json.dumps(sms_payload).encode('utf-8')
            req = urllib.request.Request(
                dispatch_url,
                data=payload_bytes,
                headers={
                    "authorization": api_key,
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                res_data = response.read().decode('utf-8')
                print(f" [LIVE SMS DISPATCH SUCCESS] Response: {res_data}")
        except Exception as e:
            print(f" [LIVE SMS DISPATCH FAILED] Error: {e}")
            status = "FAILED"
    else:
        try:
            print(f"\n==========================================")
            print(f" [FREE SMS DISPATCH] To: {receipt.donor_phone} | Message: {sms_text}")
            print(f"==========================================\n")
        except UnicodeEncodeError:
            safe_msg = sms_text.encode('ascii', 'ignore').decode('ascii')
            print(f" [FREE SMS DISPATCH] To: {receipt.donor_phone} | Message: {safe_msg}")

    if user and user.is_authenticated:
        AuditLog.objects.create(
            user=user,
            action="SMS_DISPATCH",
            model_name="FundReceipt",
            object_id=str(receipt.id),
            details=f"Dispatched SMS receipt for {receipt.donor_name} ({receipt.donor_phone}) - Status: {status}"
        )

    # Log into NotificationLog audit trail
    from audit.notifications import log_notification
    log_notification(
        recipient_phone=receipt.donor_phone or "N/A",
        recipient_name=receipt.donor_name,
        channel="SMS",
        purpose="DONATION_RECEIPT_SMS",
        message_body=sms_text,
        dispatch_url=dispatch_url,
        status=status,
        user=user
    )

    return sms_text

