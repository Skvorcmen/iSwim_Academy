from django import forms
from apps.competitions.models import Competition, Event


class CompetitionForm(forms.ModelForm):
    class Meta:
        model = Competition
        fields = [
            "name",
            "date",
            "location",
            "lanes_count",
            "regulations_pdf",
            "status",
            "registration_deadline",
            "is_open",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "registration_deadline": forms.DateTimeInput(
                attrs={"type": "datetime-local"}
            ),
        }


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "gender",
            "birth_year_from",
            "birth_year_to",
            "distance",
            "stroke",
            "order",
        ]
