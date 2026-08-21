from django.db import models
from administration.models import AuditModel, LookupValue


class Member(AuditModel):
    """Youth Committee Members Registry."""
    member_id = models.CharField(max_length=50, unique=True, help_text="e.g. MBR-2026-001")
    full_name = models.CharField(max_length=150)
    mobile_number = models.CharField(max_length=15)
    committee_position = models.CharField(max_length=100, help_text="e.g. Chief Treasurer, President")
    system_role = models.CharField(max_length=100, default="Committee Member")
    joining_date = models.DateField()
    status = models.CharField(max_length=20, default="Active")
    address = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "members_member"
        ordering = ["member_id"]

    def __str__(self):
        return f"{self.full_name} ({self.member_id})"
