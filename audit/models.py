from django.db import models
from django.contrib.auth.models import User


class AuditLog(models.Model):
    """System-wide audit trail and security log."""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    action = models.CharField(max_length=50, help_text="e.g. CREATE, UPDATE, DELETE, LOGIN")
    model_name = models.CharField(max_length=100, blank=True, null=True)
    object_id = models.CharField(max_length=100, blank=True, null=True)
    details = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_auditlog"
        ordering = ["-timestamp"]

    def __str__(self):
        user_str = self.user.username if self.user else "System"
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {user_str} - {self.action} ({self.model_name})"


class NotificationLog(models.Model):
    """Audit log tracker for SMS, WhatsApp, and OTP notification dispatches."""
    CHANNEL_CHOICES = (
        ("WHATSAPP", "WhatsApp"),
        ("SMS", "SMS"),
        ("EMAIL", "Email"),
        ("OTP", "OTP Code"),
    )
    STATUS_CHOICES = (
        ("SENT", "Sent"),
        ("DELIVERED", "Delivered"),
        ("FAILED", "Failed"),
        ("PENDING", "Pending"),
    )

    recipient_name = models.CharField(max_length=150, blank=True, default="")
    recipient_phone = models.CharField(max_length=20)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default="WHATSAPP")
    purpose = models.CharField(max_length=100, help_text="e.g. DONATION_RECEIPT, MFA_OTP, PASSWORD_RESET, HIGH_VALUE_ALERT")
    message_body = models.TextField()
    dispatch_url = models.URLField(max_length=1000, blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="SENT")
    timestamp = models.DateTimeField(auto_now_add=True)
    triggered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="notification_logs")

    class Meta:
        db_table = "audit_notificationlog"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"[{self.channel}] To: {self.recipient_phone} ({self.purpose}) - {self.status}"

