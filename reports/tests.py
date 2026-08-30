import datetime
from django.test import TestCase, Client
from django.contrib.auth.models import User
from administration.utils import amount_to_words
from administration.models import FundSource, ExpenseCategory, PaymentMethod
from funds.models import FundReceipt
from expenses.models import ExpenseVoucher
from members.models import Member


class Step3ExportsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser("admin_user", "admin@test.com", "pass123")

        self.fs = FundSource.objects.create(name="Youth Contribution", code="SRC_YOUTH")
        self.cat = ExpenseCategory.objects.create(name="Decorations", code="EXP_DECOR")
        self.pm = PaymentMethod.objects.create(name="Cash", code="PAY_CASH")

        self.receipt = FundReceipt.objects.create(
            receipt_number="RCPT-2026-999",
            donor_name="Test Donor",
            fund_source=self.fs,
            payment_method=self.pm,
            amount=10500.00,
            date_received=datetime.date(2026, 8, 20)
        )

        self.voucher = ExpenseVoucher.objects.create(
            voucher_number="EXP-2026-999",
            category=self.cat,
            vendor_name="Test Vendor",
            description="Lighting bill",
            amount_spent=4500.00,
            expense_date=datetime.date(2026, 8, 21),
            payment_method=self.pm,
            status="Approved"
        )

        self.member = Member.objects.create(
            member_id="MBR-999",
            full_name="Test Member",
            mobile_number="9988776655",
            committee_position="Treasurer",
            system_role="Treasurer",
            joining_date=datetime.date(2026, 1, 1)
        )

    def test_amount_to_words_utility(self):
        self.assertEqual(amount_to_words(10500), "Ten Thousand Five Hundred Rupees Only")
        self.assertEqual(amount_to_words(0), "Zero Rupees Only")
        self.assertEqual(amount_to_words(250000), "Two Lakh Fifty Thousand Rupees Only")

    def test_receipt_print_view(self):
        self.client.login(username="admin_user", password="pass123")
        url = f"/funds/{self.receipt.id}/print/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "RCPT-2026-999")
        self.assertContains(response, "Ten Thousand Five Hundred Rupees Only")

    def test_funds_csv_export(self):
        self.client.login(username="admin_user", password="pass123")
        response = self.client.get("/funds/export-csv/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertContains(response, "RCPT-2026-999")

    def test_expenses_csv_export(self):
        self.client.login(username="admin_user", password="pass123")
        response = self.client.get("/expenses/export-csv/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertContains(response, "EXP-2026-999")

    def test_members_csv_export(self):
        self.client.login(username="admin_user", password="pass123")
        response = self.client.get("/members/export-csv/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertContains(response, "MBR-999")

    def test_reports_csv_export(self):
        self.client.login(username="admin_user", password="pass123")
        response = self.client.get("/reports/export-csv/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertContains(response, "VINAYAKA YOUTH COMMITTEE FINANCIAL STATEMENT")
