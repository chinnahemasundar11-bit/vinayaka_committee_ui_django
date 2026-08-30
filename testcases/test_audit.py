from django.test import TestCase
from funds.models import FundReceipt
from administration.models import FundSource, PaymentMethod


class AuditTestCase(TestCase):
    def setUp(self):
        self.fs = FundSource.objects.create(name="Youth Contribution", code="SRC_QA_AUD")
        self.pm = PaymentMethod.objects.create(name="Cash", code="PAY_QA_AUD")

    def test_audit_soft_delete_and_recovery(self):
        receipt = FundReceipt.objects.create(
            receipt_number="RCPT-QA-AUD-01",
            donor_name="Audit Donor",
            donor_phone="9876543210",
            fund_source=self.fs,
            payment_method=self.pm,
            amount=7500.00,
            date_received="2026-08-25"
        )
        receipt.is_deleted = True
        receipt.save()
        self.assertTrue(receipt.is_deleted)

        receipt.is_deleted = False
        receipt.save()
        self.assertFalse(receipt.is_deleted)

    def test_notification_log_creation_and_dashboard_view(self):
        from audit.models import NotificationLog
        from audit.notifications import log_notification
        from django.contrib.auth.models import User

        admin_u = User.objects.create_superuser("aud_admin", "aud@test.com", "pass123")
        self.client.force_login(admin_u)

        initial_count = NotificationLog.objects.count()
        log_entry = log_notification(
            recipient_phone="9988776655",
            recipient_name="Test Donor",
            channel="WHATSAPP",
            purpose="DONATION_RECEIPT",
            message_body="Thank you for donation",
            dispatch_url="https://api.whatsapp.com/send",
            status="SENT",
            user=admin_u
        )
        self.assertIsNotNone(log_entry)
        self.assertEqual(NotificationLog.objects.count(), initial_count + 1)

        res = self.client.get("/audit/notifications/")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "9988776655")
        self.assertContains(res, "Test Donor")
        self.assertContains(res, "WhatsApp Receipts")
