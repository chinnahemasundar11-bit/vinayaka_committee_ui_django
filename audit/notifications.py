from audit.models import NotificationLog


def log_notification(recipient_phone, channel, purpose, message_body, recipient_name="", dispatch_url="", status="SENT", user=None):
    """
    Log an SMS, WhatsApp, Email, or OTP notification dispatch into NotificationLog audit trail.
    """
    try:
        log_entry = NotificationLog.objects.create(
            recipient_name=recipient_name or "",
            recipient_phone=str(recipient_phone or "").strip(),
            channel=channel,
            purpose=purpose,
            message_body=message_body,
            dispatch_url=dispatch_url or "",
            status=status,
            triggered_by=user if (user and user.is_authenticated) else None
        )
        return log_entry
    except Exception as e:
        print(f"Error logging notification dispatch: {e}")
        return None
