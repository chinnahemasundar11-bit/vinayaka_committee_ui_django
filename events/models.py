from django.db import models
from administration.models import AuditModel


class Event(AuditModel):
    """Festival Schedule & Program Event Registry."""
    event_id = models.CharField(max_length=50, unique=True, help_text="e.g. EVT-2026-001")
    title = models.CharField(max_length=200)
    venue_location = models.CharField(max_length=200)
    event_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    allocated_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    actual_spend = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=50, default="Planned")
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "events_event"
        ordering = ["event_date"]

    def __str__(self):
        return f"{self.title} ({self.event_date})"
