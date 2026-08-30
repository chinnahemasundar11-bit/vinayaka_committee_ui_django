from django.test import TestCase
from django.contrib.auth.models import User
from expenses.models import ExpenseVoucher
from administration.models import ExpenseCategory, PaymentMethod


class ExpensesTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("admin_exp", "exp@qa.com", "pass123")
        self.ec = ExpenseCategory.objects.create(name="Pooja Items", code="EXP_QA_POOJA")
        self.pm = PaymentMethod.objects.create(name="Cash", code="PAY_QA_CASH")

    def test_expense_voucher_lifecycle(self):
        voucher = ExpenseVoucher.objects.create(
            voucher_number="VOUCH-QA-555",
            vendor_name="Pooja Store Vendor",
            category=self.ec,
            payment_method=self.pm,
            amount_spent=3500.00,
            expense_date="2026-08-25",
            description="QA Pooja flowers",
            created_by=self.user,
            status="PENDING"
        )
        self.assertEqual(voucher.status, "PENDING")
        voucher.status = "APPROVED"
        voucher.save()
        self.assertEqual(voucher.status, "APPROVED")
