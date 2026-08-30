import json
from audit.models import AuditLog
from administration.models import SiteSetting


def get_site_setting(key, default=""):
    obj = SiteSetting.objects.filter(key=key).first()
    return obj.value if obj else default


def dispatch_high_value_event(event_type, item_number, amount, user=None, details=""):
    """
    Real-Time Webhook Alert Dispatcher.
    Triggers automated notification hooks for high-value financial transactions.
    """
    currency = get_site_setting("CURRENCY_SYMBOL", "₹")
    site_name = get_site_setting("SITE_NAME", "Vinayaka Youth Committee")

    payload = {
        "event_type": event_type, # HIGH_VALUE_DONATION, HIGH_VALUE_EXPENSE, WORKFLOW_ALERT
        "item_number": item_number,
        "amount": amount,
        "currency": currency,
        "site_name": site_name,
        "details": details,
        "triggered_by": user.username if user else "System"
    }

    # Log event into Audit Log
    AuditLog.objects.create(
        user=user,
        action=f"WEBHOOK_{event_type}",
        model_name="WebhookDispatcher",
        object_id=str(item_number),
        details=f"Real-Time Webhook Dispatched: {event_type} for {item_number} ({currency} {amount})"
    )

    # Print Webhook Dispatch payload safely for Windows console
    try:
        print(f"\n==========================================")
        print(f" [WEBHOOK DISPATCH ALERT] Event: {event_type}")
        print(f" Item: {item_number} | Amount: {currency} {amount}")
        print(f" Payload: {json.dumps(payload)}")
        print(f"==========================================\n")
    except UnicodeEncodeError:
        print(f" [WEBHOOK DISPATCH ALERT] Event: {event_type} | Item: {item_number} | Amount: INR {amount}")

    return payload
