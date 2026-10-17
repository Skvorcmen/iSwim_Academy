from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch

from apps.competitions.utils import (
    generate_application_template,
    parse_application_excel,
)
from apps.competitions.models import Competition, Application, Event, Heat, HeatLane
from apps.competitions.services import form_heats_for_competition
from apps.competitions.forms import CompetitionForm, EventForm
from django.db import models

# --- Миксины для проверки ролей ---


class CoachRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role not in ("coach", "admin"):
            return HttpResponseForbidden("Доступ запрещён — требуется роль тренера.")
        return super().dispatch(request, *args, **kwargs)


class OrganizerRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role not in ("organizer", "admin"):
            return HttpResponseForbidden(
                "Доступ запрещён — требуется роль организатора."
            )
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role != "admin":
            return HttpResponseForbidden(
                "Доступ запрещён — требуется роль администратора."
            )
        return super().dispatch(request, *args, **kwargs)


# --- Views ---

# --- Views ---


class DownloadTemplateView(CoachRequiredMixin, View):
    """Скачать Excel шаблон — только тренеры."""

    def get(self, request, competition_id):
        wb = generate_application_template()
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = (
            'attachment; filename="application_template.xlsx"'
        )
        wb.save(response)
        return response


class UploadApplicationView(CoachRequiredMixin, View):
    """Подача заявки — только тренеры."""

    def get(self, request, competition_id):
        competition = get_object_or_404(Competition, id=competition_id)

        is_admin_or_organizer = request.user.role in ("admin", "organizer")
        if not competition.is_registration_open() and not is_admin_or_organizer:
            messages.error(request, "Приём заявок закрыт.")
            return redirect("competition_list")

        return render(
            request,
            "competitions/upload_application.html",
            {
                "competition": competition,
            },
        )

    def post(self, request, competition_id):
        competition = get_object_or_404(Competition, id=competition_id)

        is_admin_or_organizer = request.user.role in ("admin", "organizer")
        if not competition.is_registration_open() and not is_admin_or_organizer:
            messages.error(request, "Приём заявок закрыт.")
            return redirect("competition_list")

        excel_file = request.FILES.get("excel_file")
        if not excel_file:
            messages.error(request, "Выберите файл для загрузки.")
            return render(
                request,
                "competitions/upload_application.html",
                {
                    "competition": competition,
                },
            )

        application = Application.objects.create(
            competition=competition,
            coach=request.user,
            excel_file=excel_file,
        )

        result = parse_application_excel(excel_file, application)

        return render(
            request,
            "competitions/upload_result.html",
            {
                "competition": competition,
                "success": result["success"],
                "errors": result["errors"],
                "athletes": result["athletes"],
            },
        )


class FormHeatsView(OrganizerRequiredMixin, View):
    """Формирование заплывов — только организаторы и админ."""

    def post(self, request, competition_id):
        competition = get_object_or_404(Competition, id=competition_id)
        form_heats_for_competition(competition)
        messages.success(request, "Заплывы успешно сформированы.")
        return redirect("view_heats", competition_id=competition_id)


class ViewHeatsView(LoginRequiredMixin, View):
    """Просмотр заплывов — все авторизованные."""

    def get(self, request, competition_id):
        competition = get_object_or_404(Competition, id=competition_id)

        heats = (
            Heat.objects.filter(event__competition=competition)
            .select_related("event")
            .prefetch_related(
                Prefetch(
                    "heatlane_set",
                    queryset=HeatLane.objects.select_related(
                        "athlete_event__athlete__team"
                    ).order_by("lane"),
                )
            )
            .order_by("number")
        )

        # Уникальные категории для навигации
        events = []
        seen_event_ids = set()
        for heat in heats:
            if heat.event.id not in seen_event_ids:
                events.append(heat.event)
                seen_event_ids.add(heat.event.id)

        return render(
            request,
            "competitions/view_heats.html",
            {
                "competition": competition,
                "heats": heats,
                "events": events,
                "can_enter_results": request.user.role in ("organizer", "admin"),
                "can_form_heats": request.user.role in ("organizer", "admin"),
                "heats_formed": heats.exists(),
            },
        )


class EnterResultsView(OrganizerRequiredMixin, View):
    """Ввод результатов — только организаторы и админ."""

    def get(self, request, heat_id):
        from apps.competitions.models import Heat

        heat = get_object_or_404(Heat, id=heat_id)
        lanes = heat.heatlane_set.select_related("athlete_event__athlete").order_by(
            "lane"
        )

        return render(
            request,
            "competitions/enter_results.html",
            {
                "heat": heat,
                "lanes": lanes,
            },
        )

    def post(self, request, heat_id):
        from apps.competitions.models import Heat
        from datetime import timedelta

        heat = get_object_or_404(Heat, id=heat_id)

        if heat.status == Heat.Status.FINISHED:
            messages.error(request, "Заплыв уже завершён, результаты изменить нельзя.")
            return redirect("enter_results", heat_id=heat_id)

        lanes = heat.heatlane_set.all()

        for lane in lanes:
            lane_id = lane.id
            dns = request.POST.get(f"dns_{lane_id}") == "on"
            dnf = request.POST.get(f"dnf_{lane_id}") == "on"
            dsq = request.POST.get(f"dsq_{lane_id}") == "on"
            time_str = request.POST.get(f"time_{lane_id}", "").strip()

            lane.dns = dns
            lane.dnf = dnf
            lane.dsq = dsq

            if time_str and not (dns or dnf or dsq):
                try:
                    digits = "".join(filter(str.isdigit, time_str))
                    digits = digits.zfill(6)
                    minutes = int(digits[0:2])
                    seconds = int(digits[2:4])
                    centiseconds = int(digits[4:6])
                    result_time = timedelta(
                        minutes=minutes, seconds=seconds, milliseconds=centiseconds * 10
                    )
                    lane.result_time = result_time

                    # Предупреждение если результат сильно лучше предвремени
                    prelim = lane.athlete_event.preliminary_time
                    if prelim and result_time < prelim * 0.7:
                        messages.warning(
                            request,
                            f"Дорожка {lane.lane} ({lane.athlete_event.athlete}): "
                            f"результат значительно лучше предвремени. Проверьте правильность ввода.",
                        )
                except (ValueError, IndexError):
                    messages.error(
                        request, f"Неверный формат времени на дорожке {lane.lane}"
                    )
                    return redirect("enter_results", heat_id=heat_id)
            else:
                lane.result_time = None

            lane.save()

        action = request.POST.get("action")

        if action == "finish":
            heat.status = Heat.Status.FINISHED
            heat.save()
            messages.success(request, f"Заплыв {heat.number} завершён.")
            return redirect("view_heats", competition_id=heat.event.competition.id)
        else:
            heat.save()
            messages.success(
                request,
                f"Результаты заплыва {heat.number} сохранены. Можно продолжить редактирование.",
            )
            return redirect("enter_results", heat_id=heat_id)


class EventResultsView(LoginRequiredMixin, View):
    """Результаты категории — все авторизованные."""

    def get(self, request, event_id):
        from apps.competitions.models import Event
        from apps.competitions.services import calculate_results_for_event

        event = get_object_or_404(Event, id=event_id)
        results = calculate_results_for_event(event)

        if results is None:
            messages.warning(request, "Не все заплывы этой категории завершены.")
            return redirect("view_heats", competition_id=event.competition.id)

        return render(
            request,
            "competitions/event_results.html",
            {
                "event": event,
                "results": results,
            },
        )


class DownloadEventResultsPdfView(LoginRequiredMixin, View):

    def get(self, request, event_id):
        from apps.competitions.models import Event
        from apps.competitions.services import calculate_results_for_event
        from apps.competitions.pdf import generate_event_results_pdf

        event = get_object_or_404(Event, id=event_id)
        results = calculate_results_for_event(event)

        if results is None:
            messages.warning(request, "Не все заплывы этой категории завершены.")
            return redirect("view_heats", competition_id=event.competition.id)

        buffer = generate_event_results_pdf(event, results)

        filename = f"results_{event.competition.id}_{event.id}.pdf"
        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class DownloadCompetitionResultsPdfView(LoginRequiredMixin, View):

    def get(self, request, competition_id):
        from apps.competitions.pdf import generate_competition_results_pdf

        competition = get_object_or_404(Competition, id=competition_id)
        buffer = generate_competition_results_pdf(competition)

        filename = f"protocol_{competition.id}_{competition.date}.pdf"
        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class CompetitionListView(LoginRequiredMixin, View):

    def get(self, request):
        competitions = Competition.objects.all().order_by("-date")
        return render(
            request,
            "competitions/competition_list.html",
            {
                "competitions": competitions,
            },
        )


class CreateCompetitionView(OrganizerRequiredMixin, View):

    def get(self, request):
        form = CompetitionForm()
        return render(
            request,
            "competitions/competition_form.html",
            {
                "form": form,
                "title": "Создать соревнование",
            },
        )

    def post(self, request):
        form = CompetitionForm(request.POST, request.FILES)
        if form.is_valid():
            competition = form.save()
            messages.success(request, f'Соревнование "{competition.name}" создано.')
            return redirect("manage_competition", competition_id=competition.id)
        return render(
            request,
            "competitions/competition_form.html",
            {
                "form": form,
                "title": "Создать соревнование",
            },
        )


class ManageCompetitionView(OrganizerRequiredMixin, View):

    def get(self, request, competition_id):
        competition = get_object_or_404(Competition, id=competition_id)
        events = Event.objects.filter(competition=competition).order_by("order")
        form = EventForm()
        return render(
            request,
            "competitions/manage_competition.html",
            {
                "competition": competition,
                "events": events,
                "form": form,
            },
        )

    def post(self, request, competition_id):
        competition = get_object_or_404(Competition, id=competition_id)
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.competition = competition
            # Автоматически проставляем порядок
            last_order = (
                Event.objects.filter(competition=competition).aggregate(
                    max_order=models.Max("order")
                )["max_order"]
                or 0
            )
            event.order = last_order + 1
            event.save()
            event = form.save(commit=False)
            event.competition = competition
            event.save()
            messages.success(request, "Категория добавлена.")
            return redirect("manage_competition", competition_id=competition_id)
        events = Event.objects.filter(competition=competition).order_by("order")
        return render(
            request,
            "competitions/manage_competition.html",
            {
                "competition": competition,
                "events": events,
                "form": form,
            },
        )


class DeleteEventView(OrganizerRequiredMixin, View):

    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        competition_id = event.competition.id
        event.delete()
        messages.success(request, "Категория удалена.")
        return redirect("manage_competition", competition_id=competition_id)


class DownloadStartProtocolPdfView(LoginRequiredMixin, View):

    def get(self, request, competition_id):
        from apps.competitions.pdf import generate_start_protocol_pdf

        competition = get_object_or_404(Competition, id=competition_id)
        buffer = generate_start_protocol_pdf(competition)

        filename = f"start_protocol_{competition.id}_{competition.date}.pdf"
        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class EditCompetitionView(OrganizerRequiredMixin, View):

    def get(self, request, competition_id):
        competition = get_object_or_404(Competition, id=competition_id)
        form = CompetitionForm(instance=competition)
        return render(
            request,
            "competitions/competition_form.html",
            {
                "form": form,
                "title": f"Редактировать — {competition.name}",
                "competition": competition,
            },
        )

    def post(self, request, competition_id):
        competition = get_object_or_404(Competition, id=competition_id)
        form = CompetitionForm(request.POST, request.FILES, instance=competition)
        if form.is_valid():
            form.save()
            messages.success(request, "Соревнование обновлено.")
            return redirect("manage_competition", competition_id=competition_id)
        return render(
            request,
            "competitions/competition_form.html",
            {
                "form": form,
                "title": f"Редактировать — {competition.name}",
                "competition": competition,
            },
        )
