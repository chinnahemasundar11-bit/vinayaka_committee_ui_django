import datetime
from django.test import TestCase
from funds.models import FundReceipt
from funds.services import build_whatsapp_receipt_url
from administration.models import FundSource, PaymentMethod


class FundsTestCase(TestCase):
    def setUp(self):
        self.fs = FundSource.objects.create(name="Youth Contribution", code="SRC_QA_FUNDS")
        self.pm = PaymentMethod.objects.create(name="Cash", code="PAY_QA_CASH")

    def test_fund_receipt_creation(self):
        receipt = FundReceipt.objects.create(
            receipt_number="RCPT-QA-101",
            donor_name="QA Donor",
            donor_phone="9876543210",
            fund_source=self.fs,
            payment_method=self.pm,
            amount=5000.00,
            date_received=datetime.date(2026, 8, 25)
        )
        self.assertIsNotNone(receipt.id)
        self.assertEqual(receipt.amount, 5000.00)

    def test_whatsapp_receipt_url_generation(self):
        receipt = FundReceipt.objects.create(
            receipt_number="RCPT-QA-WA01",
            donor_name="WhatsApp Donor",
            donor_phone="9876543210",
            fund_source=self.fs,
            payment_method=self.pm,
            amount=2500.00,
            date_received=datetime.date(2026, 8, 25)
        )
        url = build_whatsapp_receipt_url(receipt)
        self.assertIn("api.whatsapp.com", url)
