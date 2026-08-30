import datetime
from django.test import TestCase
from administration.models import FundSource, PaymentMethod
from funds.models import FundReceipt
from funds.forms import FundReceiptForm


class FundReceiptTest(TestCase):
    def setUp(self):
        self.fs = FundSource.objects.create(name="Youth Contribution", code="SRC_YOUTH")
        self.pm = PaymentMethod.objects.create(name="Cash", code="PAY_CASH")

    def test_fund_receipt_creation(self):
        receipt = FundReceipt.objects.create(
            receipt_number="RCPT-1001",
            donor_name="John Doe",
            donor_phone="9988776655",
            fund_source=self.fs,
            payment_method=self.pm,
            amount=5000.00,
            date_received=datetime.date(2026, 8, 20)
        )
        self.assertEqual(FundReceipt.objects.count(), 1)
        self.assertEqual(receipt.amount, 5000.00)
        self.assertFalse(receipt.is_deleted)

    def test_fund_receipt_form_valid(self):
        form_data = {
            "receipt_number": "RCPT-1002",
            "donor_name": "Jane Smith",
            "donor_phone": "9876543210",
            "fund_source": self.fs.id,
            "payment_method": self.pm.id,
            "amount": 2500.00,
            "date_received": "2026-08-21",
            "reference_number": "",
            "remarks": "Pooja contribution"
        }
        form = FundReceiptForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_upi_qr_code_receipt_print(self):
        upi_pm = PaymentMethod.objects.create(name="UPI / QR Code", code="PAY_UPI", icon_name="bi-qr-code-scan")
        receipt = FundReceipt.objects.create(
            receipt_number="RCPT-UPI-01",
            donor_name="UPI Donor",
            donor_phone="9988771122",
            fund_source=self.fs,
            payment_method=upi_pm,
            amount=1008.00,
            date_received=datetime.date(2026, 8, 22)
        )
        from django.test import Client
        from django.contrib.auth.models import User
        client = Client()
        user = User.objects.create_superuser("admin_upi", "upi@test.com", "pass123")
        client.force_login(user)

        response = client.get(f"/funds/{receipt.id}/print/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Direct Payment via UPI")
        self.assertContains(response, "api.qrserver.com")

    def test_whatsapp_and_sms_service(self):
        from funds.services import build_whatsapp_receipt_url, send_sms_receipt_notification, format_phone_for_whatsapp
        receipt = FundReceipt.objects.create(
            receipt_number="RCPT-WA-01",
            donor_name="WhatsApp Donor",
            donor_phone="9876543210",
            fund_source=self.fs,
            payment_method=self.pm,
            amount=2100.00,
            date_received=datetime.date(2026, 8, 23)
        )
        self.assertEqual(format_phone_for_whatsapp("9876543210"), "919876543210")

        wa_url = build_whatsapp_receipt_url(receipt)
        self.assertIn("https://api.whatsapp.com/send", wa_url)
        self.assertIn("919876543210", wa_url)

        sms_msg = send_sms_receipt_notification(receipt)
        self.assertIn("2100.00", sms_msg)
        self.assertIn("WhatsApp Donor", sms_msg)

