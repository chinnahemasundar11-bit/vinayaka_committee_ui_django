from django.test import TestCase
from django.contrib.auth.models import User
from events.models import Event


class EventsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("admin_evt", "evt@qa.com", "pass123")

    def test_festival_event_creation(self):
        event = Event.objects.create(
            event_id="EVT-QA-001",
            title="Ganesh Immersion Procession",
            event_date="2026-08-30",
            venue_location="Main Temple Pandal",
            allocated_budget=150000.00,
            actual_spend=45000.00,
            status="SCHEDULED",
            created_by=self.user
        )
        self.assertIsNotNone(event.id)
        self.assertEqual(event.status, "SCHEDULED")
