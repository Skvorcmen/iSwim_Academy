from django.contrib.auth.forms import UserCreationForm
from apps.users.models import User
from django import forms


class RegisterForm(UserCreationForm):

    class Meta:
        model = User
        fields = ("username", "email", "role", "password1", "password2")
