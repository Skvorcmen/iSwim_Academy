from django.contrib.auth.forms import UserCreationForm
from apps.users.models import User
from django import forms


class RegisterForm(UserCreationForm):

    class Meta:
        model = User
        fields = ("username", "email", "role", "password1", "password2")


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        labels = {
            "first_name": "Имя",
            "last_name": "Фамилия",
            "email": "Email",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }
