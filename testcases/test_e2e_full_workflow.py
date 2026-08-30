from django.test import TestCase, Client
from django.contrib.auth.models import User
from funds.models import FundReceipt
from expenses.models import ExpenseVoucher
from administration.models import FundSource, PaymentMethod, ExpenseCategory


class E2EWorkflowTestCase(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser("admin_e2e", "e2e@qa.com", "pass123")
        self.fs = FundSource.objects.create(name="Youth Contribution", code="SRC_QA_E2E")
        self.pm = PaymentMethod.objects.create(name="Cash", code="PAY_QA_E2E")
        self.ec = ExpenseCategory.objects.create(name="Decorations", code="EXP_QA_E2E")

    def test_end_to_end_festival_finance_lifecycle(self):
        client = Client()
        client.force_login(self.admin_user)

        # 1. Collect receipt
        receipt = FundReceipt.objects.create(
            receipt_number="RCPT-E2E-999",
            donor_name="E2E Donor",
            donor_phone="9988776655",
            fund_source=self.fs,
            payment_method=self.pm,
            amount=10000.00,
            date_received="2026-08-25"
        )
        self.assertIsNotNone(receipt.id)

        # 2. Spend vendor voucher
        voucher = ExpenseVoucher.objects.create(
            voucher_number="VOUCH-E2E-999",
            vendor_name="E2E Decorators",
            category=self.ec,
            payment_method=self.pm,
            amount_spent=5000.00,
            expense_date="2026-08-25",
            created_by=self.admin_user,
            status="APPROVED"
        )
        self.assertEqual(voucher.status, "APPROVED")

        # 3. Access AI Expense Predictor dashboard
        res_ai = client.get("/administration/analytics/expense-predictor/")
        self.assertEqual(res_ai.status_code, 200)

        # 4. Access QA Test Dashboard
        res_qa = client.get("/qa-dashboard/")
        self.assertEqual(res_qa.status_code, 200)
