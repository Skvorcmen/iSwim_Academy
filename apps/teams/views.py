from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.teams.models import Athlete, LinkRequest


class AthleteSearchView(LoginRequiredMixin, View):
    """Атлет ищет себя в базе спортсменов."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role != "athlete":
            return HttpResponseForbidden("Раздел доступен роли «Спортсмен».")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        last_name = request.GET.get("last_name", "").strip()
        birth_year = request.GET.get("birth_year", "").strip()
        results = []
        searched = False

        if last_name or birth_year:
            searched = True
            if len(last_name) < 2 or not birth_year.isdigit():
                messages.warning(request, "Укажите фамилию (от 2 букв) и год рождения.")
            else:
                results = Athlete.objects.filter(
                    last_name__icontains=last_name,
                    birth_year=int(birth_year),
                    user__isnull=True,
                ).select_related("team")[:20]

        pending_ids = set(
            request.user.link_requests.filter(
                status=LinkRequest.Status.PENDING
            ).values_list("athlete_id", flat=True)
        )
        return render(
            request,
            "teams/athlete_search.html",
            {
                "results": results,
                "searched": searched,
                "pending_ids": pending_ids,
                "my_requests": request.user.link_requests.select_related("athlete"),
                "my_profiles": request.user.athlete_profiles.all(),
            },
        )


class LinkRequestCreateView(LoginRequiredMixin, View):

    def post(self, request, athlete_id):
        if request.user.role != "athlete":
            return HttpResponseForbidden()
        athlete = get_object_or_404(Athlete, id=athlete_id, user__isnull=True)
        _, created = LinkRequest.objects.get_or_create(
            user=request.user, athlete=athlete, status=LinkRequest.Status.PENDING
        )
        if created:
            messages.success(request, "Заявка отправлена тренеру спортсмена.")
        else:
            messages.info(request, "Заявка уже отправлена.")
        return redirect("athlete_search")


class CoachLinkRequestsView(LoginRequiredMixin, View):
    """Тренер видит заявки на привязку своих спортсменов. Админ видит все."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role not in (
            "coach",
            "admin",
        ):
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        qs = LinkRequest.objects.filter(
            status=LinkRequest.Status.PENDING
        ).select_related("user", "athlete", "athlete__team")
        if request.user.role != "admin":
            qs = qs.filter(athlete__coach=request.user)
        return render(request, "teams/link_requests.html", {"requests": qs})


class LinkRequestReviewView(LoginRequiredMixin, View):

    def post(self, request, pk, action):
        link = get_object_or_404(
            LinkRequest.objects.select_related("athlete"),
            pk=pk,
            status=LinkRequest.Status.PENDING,
        )
        is_admin = request.user.role == "admin"
        is_athlete_coach = (
            request.user.role == "coach" and link.athlete.coach_id == request.user.id
        )
        if not (is_admin or is_athlete_coach):
            return HttpResponseForbidden()

        if action == "approve":
            athlete = link.athlete
            if athlete.user_id:
                messages.error(
                    request, "Этот спортсмен уже привязан к другому профилю."
                )
            else:
                athlete.user = link.user
                athlete.save(update_fields=["user", "updated_at"])
                link.status = LinkRequest.Status.APPROVED
                # остальные заявки на этого спортсмена закрываем
                LinkRequest.objects.filter(
                    athlete=athlete, status=LinkRequest.Status.PENDING
                ).exclude(pk=link.pk).update(status=LinkRequest.Status.REJECTED)
                messages.success(request, "Привязка подтверждена.")
        else:
            link.status = LinkRequest.Status.REJECTED
            messages.info(request, "Заявка отклонена.")

        link.reviewed_by = request.user
        link.save(update_fields=["status", "reviewed_by", "updated_at"])
        return redirect("coach_link_requests")
