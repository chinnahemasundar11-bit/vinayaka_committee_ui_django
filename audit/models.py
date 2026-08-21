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
