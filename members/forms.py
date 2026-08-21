from django import forms
from .models import Member


class MemberForm(forms.ModelForm):
    """ModelForm for recording & updating Youth Committee Members."""
    class Meta:
        model = Member
        fields = ["member_id", "full_name", "mobile_number", "committee_position", "system_role", "joining_date", "status", "address"]
        widgets = {
            "member_id": forms.TextInput(attrs={"class": "form-control", "required": "required"}),
            "full_name": forms.TextInput(attrs={"class": "form-control", "required": "required"}),
            "mobile_number": forms.TextInput(attrs={"class": "form-control", "required": "required"}),
            "committee_position": forms.TextInput(attrs={"class": "form-control", "required": "required"}),
            "system_role": forms.TextInput(attrs={"class": "form-control", "required": "required"}),
            "joining_date": forms.DateInput(attrs={"class": "form-control", "type": "date", "required": "required"}),
            "status": forms.Select(attrs={"class": "form-select"}, choices=[("Active", "Active"), ("Inactive", "Inactive")]),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
