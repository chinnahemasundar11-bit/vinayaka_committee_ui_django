from django import forms
from .models import FundReceipt
from administration.models import FundSource, PaymentMethod


class FundReceiptForm(forms.ModelForm):
    """ModelForm for recording & updating Fund Receipts."""
    fund_source = forms.ModelChoiceField(
        queryset=FundSource.objects.filter(is_active=True),
        widget=forms.Select(attrs={"class": "form-select", "required": "required"})
    )
    payment_method = forms.ModelChoiceField(
        queryset=PaymentMethod.objects.filter(is_active=True),
        widget=forms.Select(attrs={"class": "form-select", "required": "required"})
    )

    class Meta:
        model = FundReceipt
        fields = ["receipt_number", "donor_name", "donor_phone", "fund_source", "payment_method", "amount", "date_received", "reference_number", "remarks"]
        widgets = {
            "receipt_number": forms.TextInput(attrs={"class": "form-control", "required": "required"}),
            "donor_name": forms.TextInput(attrs={"class": "form-control", "required": "required"}),
            "donor_phone": forms.TextInput(attrs={"class": "form-control"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "required": "required"}),
            "date_received": forms.DateInput(attrs={"class": "form-control", "type": "date", "required": "required"}),
            "reference_number": forms.TextInput(attrs={"class": "form-control"}),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
