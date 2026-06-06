from django.views.generic import CreateView, TemplateView
from django.urls import reverse_lazy
from apps.users.forms import RegisterForm
from django.contrib.auth.mixins import LoginRequiredMixin


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("home")


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "users/profile.html"
    login_url = "accounts/login"
