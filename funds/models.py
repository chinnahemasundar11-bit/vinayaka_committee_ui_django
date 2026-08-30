from django.db import models
from administration.models import AuditModel, FundSource, PaymentMethod


class FundReceipt(AuditModel):
    """Fund Receipts & Contributions Financial Ledger."""
    receipt_number = models.CharField(max_length=50, unique=True, db_index=True)
    donor_name = models.CharField(max_length=150)
    donor_phone = models.CharField(max_length=15, blank=True, null=True, db_index=True)
    fund_source = models.ForeignKey(FundSource, on_delete=models.PROTECT, related_name="receipts")
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT, related_name="fund_receipts")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date_received = models.DateField(db_index=True)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "funds_fund_receipt"
        ordering = ["-date_received", "-id"]

    def __str__(self):
        return f"{self.receipt_number} - {self.donor_name} (₹{self.amount})"
