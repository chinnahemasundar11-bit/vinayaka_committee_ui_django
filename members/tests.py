import datetime
from django.test import TestCase
from members.models import Member
from members.forms import MemberForm


class MemberTest(TestCase):
    def test_member_creation(self):
        member = Member.objects.create(
            member_id="MBR-2026-101",
            full_name="Rajesh Sharma",
            mobile_number="9876543210",
            committee_position="President",
            system_role="Super Admin",
            joining_date=datetime.date(2026, 1, 1),
            status="Active"
        )
        self.assertEqual(Member.objects.count(), 1)
        self.assertEqual(str(member), "Rajesh Sharma (MBR-2026-101)")

    def test_member_form_valid(self):
        form_data = {
            "member_id": "MBR-2026-102",
            "full_name": "Suresh Reddy",
            "mobile_number": "9123456789",
            "committee_position": "Treasurer",
            "system_role": "Treasurer",
            "joining_date": "2026-02-01",
            "status": "Active",
            "address": "Hyderabad"
        }
        form = MemberForm(data=form_data)
        self.assertTrue(form.is_valid())
