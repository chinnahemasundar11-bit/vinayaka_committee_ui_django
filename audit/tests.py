import datetime
from django.test import TestCase, Client
from django.contrib.auth.models import User
from funds.models import FundReceipt
from administration.models import FundSource, PaymentMethod


class AuditRestoreTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser("audit_admin", "admin@audit.com", "pass123")
        self.fs = FundSource.objects.create(name="Donor Fund", code="SRC_DONOR")
        self.pm = PaymentMethod.objects.create(name="Cash", code="PAY_CASH")

    def test_soft_delete_and_restore_fund_receipt(self):
        receipt = FundReceipt.objects.create(
            receipt_number="RCPT-RESTORE-01",
            donor_name="Restore Donor",
            donor_phone="9988776655",
            fund_source=self.fs,
            payment_method=self.pm,
            amount=1500.00,
            date_received=datetime.date(2026, 8, 20)
        )
        self.assertFalse(receipt.is_deleted)

        # Soft delete receipt
        receipt.delete()
        self.assertTrue(receipt.is_deleted)
        self.assertEqual(FundReceipt.objects.count(), 0)
        self.assertEqual(FundReceipt.all_objects.count(), 1)

        # Force login as Super Admin
        self.client.force_login(self.admin)

        # Trigger 1-click restore
        response = self.client.post(f"/audit/restore/FundReceipt/{receipt.id}/")
        self.assertRedirects(response, "/audit/?action=DELETE")

        # Verify receipt is restored (is_deleted=False)
        receipt.refresh_from_db()
        self.assertFalse(receipt.is_deleted)
        self.assertEqual(FundReceipt.objects.count(), 1)
