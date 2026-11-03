from django.contrib.auth.forms import UserCreationForm
from django import forms
from apps.users.models import User, RoleRequest


class RegisterForm(UserCreationForm):
    role = forms.ChoiceField(
        label="Роль",
        choices=[("fan", "Болельщик"), ("athlete", "Спортсмен")],
        initial="fan",
    )

    class Meta:
        model = User
        fields = ("username", "email", "role", "password1", "password2")


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        labels = {"first_name": "Имя", "last_name": "Фамилия", "email": "Email"}
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }


class RoleRequestForm(forms.ModelForm):
    ALLOWED_EXT = (".pdf", ".jpg", ".jpeg", ".png")
    MAX_SIZE = 5 * 1024 * 1024

    class Meta:
        model = RoleRequest
        fields = ("diploma_scan", "comment")
        labels = {
            "diploma_scan": "Скан диплома (PDF, JPG, PNG до 5 МБ)",
            "comment": "Комментарий",
        }
        widgets = {
            "diploma_scan": forms.FileInput(attrs={"class": "form-control"}),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def clean_diploma_scan(self):
        f = self.cleaned_data["diploma_scan"]
        if not f.name.lower().endswith(self.ALLOWED_EXT):
            raise forms.ValidationError("Допустимы только PDF, JPG и PNG.")
        if f.size > self.MAX_SIZE:
            raise forms.ValidationError("Файл больше 5 МБ.")
        return f
