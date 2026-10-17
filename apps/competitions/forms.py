from django import forms
from apps.competitions.models import Competition, Event
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
        labels = {
            "name": "Название",
            "date": "Дата",
            "location": "Место проведения",
            "lanes_count": "Количество дорожек",
            "regulations_pdf": "Положение (PDF)",
            "status": "Статус",
            "registration_deadline": "Дедлайн приёма заявок",
            "is_open": "Открытое соревнование",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "lanes_count": forms.NumberInput(attrs={"class": "form-control"}),
            "regulations_pdf": forms.FileInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "registration_deadline": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "is_open": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        help_texts = {
            "is_open": "Открытое соревнование доступно для команд из других клубов. Внутреннее — только для спортсменов академии iSwim.",
            "registration_deadline": "Дата и время после которых подача заявок будет закрыта.",
            "lanes_count": "Количество дорожек в бассейне — влияет на формирование заплывов.",
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
        ]
        labels = {
            "gender": "Пол",
            "birth_year_from": "Год рождения от",
            "birth_year_to": "Год рождения до",
            "distance": "Дистанция (м)",
            "stroke": "Стиль",
        }
        widgets = {
            "gender": forms.Select(attrs={"class": "form-select"}),
            "birth_year_from": forms.NumberInput(attrs={"class": "form-control"}),
            "birth_year_to": forms.NumberInput(attrs={"class": "form-control"}),
            "distance": forms.NumberInput(attrs={"class": "form-control"}),
            "stroke": forms.Select(attrs={"class": "form-select"}),
        }


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
            "date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"
            ),
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
        ]
        labels = {
            "gender": "Пол",
            "birth_year_from": "Год рождения от",
            "birth_year_to": "Год рождения до",
            "distance": "Дистанция (м)",
            "stroke": "Стиль",
            "order": "Порядок",
        }
