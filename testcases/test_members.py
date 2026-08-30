import random
from django.test import TestCase
from members.models import Member


class MembersTestCase(TestCase):
    def test_member_registration(self):
        member = Member.objects.create(
            member_id=f"MBR-QA-{random.randint(1000, 9999)}",
            full_name="Rajesh Kumar",
            mobile_number=f"9{random.randint(100000009, 999999999)}",
            committee_position="Treasurer",
            joining_date="2026-08-25",
            status="Active"
        )
        self.assertIsNotNone(member.id)
        self.assertEqual(member.committee_position, "Treasurer")
