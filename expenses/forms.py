from django import forms
from .models import ExpenseVoucher
from administration.models import ExpenseCategory, PaymentMethod


class ExpenseVoucherForm(forms.ModelForm):
    """ModelForm for recording & updating Expense Vouchers."""
    category = forms.ModelChoiceField(
        queryset=ExpenseCategory.objects.filter(is_active=True),
        widget=forms.Select(attrs={"class": "form-select", "required": "required"})
    )
    payment_method = forms.ModelChoiceField(
        queryset=PaymentMethod.objects.filter(is_active=True),
        widget=forms.Select(attrs={"class": "form-select", "required": "required"})
    )

    class Meta:
        model = ExpenseVoucher
        fields = ["voucher_number", "category", "vendor_name", "description", "amount_spent", "expense_date", "payment_method", "status"]
        widgets = {
            "voucher_number": forms.TextInput(attrs={"class": "form-control", "required": "required"}),
            "vendor_name": forms.TextInput(attrs={"class": "form-control", "required": "required"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "required": "required"}),
            "amount_spent": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "required": "required"}),
            "expense_date": forms.DateInput(attrs={"class": "form-control", "type": "date", "required": "required"}),
        }
