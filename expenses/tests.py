import datetime
from django.test import TestCase
from administration.models import ExpenseCategory, PaymentMethod
from expenses.models import ExpenseVoucher
from expenses.forms import ExpenseVoucherForm


class ExpenseVoucherTest(TestCase):
    def setUp(self):
        self.cat = ExpenseCategory.objects.create(name="Decorations", code="EXP_DECOR")
        self.pm = PaymentMethod.objects.create(name="UPI", code="PAY_UPI")

    def test_expense_voucher_creation(self):
        voucher = ExpenseVoucher.objects.create(
            voucher_number="EXP-1001",
            category=self.cat,
            vendor_name="Venkateswara Traders",
            description="Flower decoration items",
            amount_spent=3500.00,
            expense_date=datetime.date(2026, 8, 22),
            payment_method=self.pm,
            status="Approved"
        )
        self.assertEqual(ExpenseVoucher.objects.count(), 1)
        self.assertEqual(voucher.amount_spent, 3500.00)

    def test_expense_voucher_form_valid(self):
        form_data = {
            "voucher_number": "EXP-1002",
            "category": self.cat.id,
            "vendor_name": "ABC Lights",
            "description": "Lighting setup for 5 days",
            "amount_spent": 12000.00,
            "expense_date": "2026-08-22",
            "payment_method": self.pm.id,
            "status": "Approved"
        }
        form = ExpenseVoucherForm(data=form_data)
        self.assertTrue(form.is_valid())
