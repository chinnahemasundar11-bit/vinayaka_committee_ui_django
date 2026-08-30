import datetime
from django.test import TestCase
from events.models import Event
from events.forms import EventForm


class EventTest(TestCase):
    def test_event_creation(self):
        evt = Event.objects.create(
            event_id="EVT-2026-101",
            title="Ganesh Sthapana Pooja",
            venue_location="Main Temple Mandapam",
            event_date=datetime.date(2026, 8, 20),
            allocated_budget=20000.00,
            actual_spend=18500.00,
            status="Planned"
        )
        self.assertEqual(Event.objects.count(), 1)
        self.assertEqual(str(evt), "Ganesh Sthapana Pooja (2026-08-20)")

    def test_event_form_valid(self):
        form_data = {
            "event_id": "EVT-2026-102",
            "title": "Annasantharpana Mahaprasadam",
            "venue_location": "Community Grounds",
            "event_date": "2026-08-24",
            "allocated_budget": 50000.00,
            "actual_spend": 45000.00,
            "status": "Planned",
            "description": "Mass lunch distribution"
        }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())
