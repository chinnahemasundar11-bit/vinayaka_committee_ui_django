from django.db import models
from administration.models import AuditModel, ExpenseCategory, PaymentMethod


class ExpenseVoucher(AuditModel):
    """Expense Vouchers & Vendor Outflows Financial Ledger."""
    voucher_number = models.CharField(max_length=50, unique=True, db_index=True)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name="expenses")
    vendor_name = models.CharField(max_length=150)
    description = models.TextField()
    amount_spent = models.DecimalField(max_digits=12, decimal_places=2)
    expense_date = models.DateField(db_index=True)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT, related_name="expense_vouchers")
    status = models.CharField(max_length=50, default="Approved", db_index=True)

    class Meta:
        db_table = "expenses_expense_voucher"
        ordering = ["-expense_date", "-id"]

    def __str__(self):
        return f"{self.voucher_number} - {self.vendor_name} (₹{self.amount_spent})"
