from django.views.generic import CreateView, TemplateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from django.db.models import Count
from apps.competitions.models import Application
from django.shortcuts import redirect
from django.views.generic import CreateView
from apps.users.forms import RegisterForm, ProfileEditForm, RoleRequestForm
from apps.users.models import RoleRequest
from apps.competitions.models import Application, AthleteEvent, HeatLane, Heat
from apps.competitions.services import calculate_results_for_event
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views import View


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("home")


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "users/profile.html"
    login_url = "/accounts/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.role == "coach":
            context["applications"] = (
                Application.objects.filter(coach=user)
                .select_related("competition")
                .annotate(
                    athletes_count=Count("athleteevent__athlete", distinct=True),
                    starts_count=Count("athleteevent", distinct=True),
                )
                .order_by("-competition__date")
            )

        context["role_request"] = user.role_requests.first()
        context["can_request_coach"] = user.role in ("fan", "athlete")
        if user.role == "athlete":
            context["my_results"] = self._build_results(user)
        return context

    def _build_results(self, user):
        profiles = user.athlete_profiles.all()
        rows = []
        starts = (
            AthleteEvent.objects.filter(athlete__in=profiles)
            .select_related("athlete", "event", "event__competition")
            .order_by("-event__competition__date", "event__order")
        )
        for ae in starts:
            lane = (
                HeatLane.objects.filter(
                    athlete_event=ae, heat__status=Heat.Status.FINISHED
                )
                .select_related("heat")
                .first()
            )
            if not lane:
                continue

            place = None
            if not ae.is_out_of_competition and not (lane.dns or lane.dnf or lane.dsq):
                results = calculate_results_for_event(ae.event)
                if results:
                    for r in results:
                        if r["athlete"].id == ae.athlete_id:
                            place = r["place"]
                            break

            status = None
            if lane.dns:
                status = "DNS"
            elif lane.dnf:
                status = "DNF"
            elif lane.dsq:
                status = "DSQ"
            elif ae.is_out_of_competition:
                status = "ВК"

            rows.append(
                {
                    "athlete": ae.athlete,
                    "competition": ae.event.competition,
                    "event": ae.event,
                    "time": lane.result_time,
                    "place": place,
                    "status": status,
                }
            )
        return rows


class ProfileEditView(LoginRequiredMixin, UpdateView):
    form_class = ProfileEditForm
    template_name = "users/profile_edit.html"
    success_url = reverse_lazy("profile")
    login_url = "/accounts/login/"

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Профиль обновлён.")
        return super().form_valid(form)


class UserPasswordChangeView(PasswordChangeView):
    template_name = "users/password_change.html"
    success_url = reverse_lazy("user_password_change_done")


class UserPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = "users/password_change_done.html"


class RoleRequestCreateView(LoginRequiredMixin, CreateView):
    form_class = RoleRequestForm
    template_name = "users/role_request.html"
    success_url = reverse_lazy("profile")
    login_url = "/accounts/login/"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.role not in ("fan", "athlete"):
                messages.info(request, "У вас уже есть расширенная роль.")
                return redirect("profile")
            if request.user.role_requests.filter(
                status=RoleRequest.Status.PENDING
            ).exists():
                messages.info(request, "Ваша заявка уже на рассмотрении.")
                return redirect("profile")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(
            self.request, "Заявка отправлена. Администратор рассмотрит её."
        )
        return super().form_valid(form)


class DiplomaDownloadView(LoginRequiredMixin, View):
    """Скан диплома видит только администратор."""

    login_url = "/accounts/login/"

    def get(self, request, pk):
        if not (request.user.role == "admin" or request.user.is_superuser):
            return HttpResponseForbidden("Доступ запрещён.")
        role_request = get_object_or_404(RoleRequest, pk=pk)
        try:
            file = role_request.diploma_scan.open("rb")
        except (FileNotFoundError, ValueError):
            raise Http404("Файл не найден")
        return FileResponse(file)
