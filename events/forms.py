from django import forms
from .models import Event


class EventForm(forms.ModelForm):
    """ModelForm for recording & updating Festival Events."""
    class Meta:
        model = Event
        fields = ["event_id", "title", "venue_location", "event_date", "start_time", "end_time", "allocated_budget", "actual_spend", "status", "description"]
        widgets = {
            "event_id": forms.TextInput(attrs={"class": "form-control", "required": "required"}),
            "title": forms.TextInput(attrs={"class": "form-control", "required": "required"}),
            "venue_location": forms.TextInput(attrs={"class": "form-control", "required": "required"}),
            "event_date": forms.DateInput(attrs={"class": "form-control", "type": "date", "required": "required"}),
            "start_time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "end_time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "allocated_budget": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "required": "required"}),
            "actual_spend": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "status": forms.Select(attrs={"class": "form-select"}, choices=[("Planned", "Planned"), ("Ongoing", "Ongoing"), ("Completed", "Completed")]),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
