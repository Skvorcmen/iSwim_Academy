import io
from datetime import date, timedelta

import openpyxl
from django.test import TestCase
from django.urls import reverse

from apps.competitions.models import (
    Application,
    AthleteEvent,
    Competition,
    Event,
    Heat,
    HeatLane,
)
from apps.competitions.utils import parse_application_excel
from apps.teams.models import Athlete, LinkRequest, Team
from apps.users.models import User

PWD = "TestPass123!"


def make_user(username, role="fan"):
    return User.objects.create_user(username=username, password=PWD, role=role)


def make_excel(rows):
    """rows: список по 9 значений. Строки 1-2 это заголовок и пример."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["h"] * 9)
    ws.append(["пример"] * 9)
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


class BaseCompetitionTest(TestCase):
    def setUp(self):
        self.coach = make_user("coach1", "coach")
        self.competition = Competition.objects.create(
            name="Кубок",
            date=date(2026, 12, 1),
            location="Астана",
            lanes_count=6,
            status=Competition.Status.REGISTRATION,
        )
        self.event_free = Event.objects.create(
            competition=self.competition,
            gender="male",
            birth_year_from=2010,
            birth_year_to=2012,
            distance=50,
            stroke="freestyle",
            order=1,
        )
        self.event_back = Event.objects.create(
            competition=self.competition,
            gender="male",
            birth_year_from=2010,
            birth_year_to=2012,
            distance=50,
            stroke="backstroke",
            order=2,
        )
        self.application = Application.objects.create(
            competition=self.competition, coach=self.coach
        )

    def parse(self, rows):
        return parse_application_excel(make_excel(rows), self.application)


class ExcelParserTest(BaseCompetitionTest):
    def row(
        self,
        last="Иванов",
        first="Иван",
        year=2011,
        stroke="кроль",
        prelim="00:32.45",
        okc="нет",
    ):
        return [last, first, year, "М", "iSwim", 50, stroke, prelim, okc]

    def test_one_athlete_two_distances_one_record(self):
        result = self.parse([self.row(), self.row(stroke="спина")])
        self.assertEqual(Athlete.objects.count(), 1)
        self.assertEqual(AthleteEvent.objects.count(), 2)
        self.assertEqual(result["success"], 2)
        self.assertEqual(result["athletes_count"], 1)

    def test_repeat_upload_goes_to_skipped(self):
        self.parse([self.row()])
        result = self.parse([self.row()])
        self.assertEqual(result["success"], 0)
        self.assertEqual(len(result["skipped"]), 1)
        self.assertEqual(result["errors"], [])
        self.assertEqual(AthleteEvent.objects.count(), 1)

    def test_mixed_alphabet_rejected(self):
        # латинская B + кириллица
        result = self.parse([self.row(last="Bонова")])
        self.assertEqual(Athlete.objects.count(), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("раскладку", result["errors"][0])

    def test_pure_latin_name_allowed(self):
        self.parse([self.row(last="Ivanov", first="Ivan")])
        self.assertEqual(Athlete.objects.count(), 1)

    def test_empty_prelim_allowed(self):
        self.parse([self.row(prelim=None)])
        self.assertIsNone(AthleteEvent.objects.get().preliminary_time)

    def test_prelim_time_exact(self):
        self.parse([self.row(prelim="00:32.45")])
        self.assertEqual(
            AthleteEvent.objects.get().preliminary_time,
            timedelta(seconds=32, milliseconds=450),
        )

    def test_okc_flag(self):
        self.parse([self.row(okc="да")])
        self.assertTrue(AthleteEvent.objects.get().is_out_of_competition)

    def test_no_event_for_birth_year(self):
        result = self.parse([self.row(year=2000)])
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(Athlete.objects.count(), 0)

    def test_existing_athlete_reused_across_competitions(self):
        self.parse([self.row()])
        other = Competition.objects.create(
            name="Второе", date=date(2027, 1, 1), location="Алматы"
        )
        Event.objects.create(
            competition=other,
            gender="male",
            birth_year_from=2010,
            birth_year_to=2012,
            distance=50,
            stroke="freestyle",
            order=1,
        )
        app2 = Application.objects.create(competition=other, coach=self.coach)
        result = parse_application_excel(make_excel([self.row()]), app2)
        self.assertEqual(Athlete.objects.count(), 1)
        self.assertEqual(result["stats"]["existing"], 1)


class LinkRequestTest(TestCase):
    def setUp(self):
        self.coach = make_user("coach1", "coach")
        self.other_coach = make_user("coach2", "coach")
        self.admin = make_user("adm", "admin")
        self.user = make_user("ath", "athlete")
        team = Team.objects.create(name="iSwim", city="")
        self.athlete = Athlete.objects.create(
            first_name="Иван",
            last_name="Иванов",
            birth_year=2011,
            gender="male",
            team=team,
            coach=self.coach,
        )
        self.link = LinkRequest.objects.create(user=self.user, athlete=self.athlete)

    def review(self, username, action="approve"):
        self.client.login(username=username, password=PWD)
        return self.client.post(
            reverse("link_request_review", args=[self.link.pk, action])
        )

    def test_own_coach_can_approve(self):
        self.review("coach1")
        self.athlete.refresh_from_db()
        self.assertEqual(self.athlete.user, self.user)
        self.link.refresh_from_db()
        self.assertEqual(self.link.status, LinkRequest.Status.APPROVED)

    def test_other_coach_forbidden(self):
        response = self.review("coach2")
        self.assertEqual(response.status_code, 403)
        self.athlete.refresh_from_db()
        self.assertIsNone(self.athlete.user)

    def test_admin_can_approve(self):
        self.review("adm")
        self.athlete.refresh_from_db()
        self.assertEqual(self.athlete.user, self.user)

    def test_athlete_cannot_approve_self(self):
        response = self.review("ath")
        self.assertEqual(response.status_code, 403)

    def test_reject_does_not_link(self):
        self.review("coach1", "reject")
        self.athlete.refresh_from_db()
        self.assertIsNone(self.athlete.user)

    def test_already_linked_athlete_not_overwritten(self):
        other_user = make_user("ath2", "athlete")
        self.athlete.user = other_user
        self.athlete.save()
        self.review("coach1")
        self.athlete.refresh_from_db()
        self.assertEqual(self.athlete.user, other_user)

    def test_search_only_for_athlete_role(self):
        self.client.login(username="coach1", password=PWD)
        self.assertEqual(self.client.get(reverse("athlete_search")).status_code, 403)


class HeatFlowTest(BaseCompetitionTest):
    def setUp(self):
        super().setUp()
        self.organizer = make_user("org", "organizer")
        ath = Athlete.objects.create(
            first_name="Иван",
            last_name="Иванов",
            birth_year=2011,
            gender="male",
            team=Team.objects.create(name="T", city=""),
            coach=self.coach,
        )
        self.ath = ath
        self.ae1 = AthleteEvent.objects.create(
            athlete=ath,
            event=self.event_free,
            application=self.application,
            preliminary_time=timedelta(seconds=40),
        )
        self.heat = Heat.objects.create(event=self.event_free, number=1)
        self.lane1 = HeatLane.objects.create(
            heat=self.heat, athlete_event=self.ae1, lane=3
        )

    def finish_url(self):
        return reverse("finish_competition", args=[self.competition.id])

    def test_cannot_finish_with_unfinished_heats(self):
        self.client.login(username="org", password=PWD)
        self.client.post(self.finish_url())
        self.competition.refresh_from_db()
        self.assertNotEqual(self.competition.status, Competition.Status.FINISHED)

    def test_can_finish_when_all_heats_finished(self):
        self.heat.status = Heat.Status.FINISHED
        self.heat.save()
        self.client.login(username="org", password=PWD)
        self.client.post(self.finish_url())
        self.competition.refresh_from_db()
        self.assertEqual(self.competition.status, Competition.Status.FINISHED)

    def test_cannot_finish_without_heats(self):
        Heat.objects.all().delete()
        self.client.login(username="org", password=PWD)
        self.client.post(self.finish_url())
        self.competition.refresh_from_db()
        self.assertNotEqual(self.competition.status, Competition.Status.FINISHED)

    def test_coach_cannot_finish_competition(self):
        self.heat.status = Heat.Status.FINISHED
        self.heat.save()
        self.client.login(username="coach1", password=PWD)
        response = self.client.post(self.finish_url())
        self.assertEqual(response.status_code, 403)

    def test_all_dns_keeps_entered_times(self):
        ath2 = Athlete.objects.create(
            first_name="Пётр",
            last_name="Петров",
            birth_year=2011,
            gender="male",
            team=self.ath.team,
            coach=self.coach,
        )
        ae2 = AthleteEvent.objects.create(
            athlete=ath2,
            event=self.event_free,
            application=self.application,
        )
        lane2 = HeatLane.objects.create(heat=self.heat, athlete_event=ae2, lane=4)
        self.lane1.result_time = timedelta(seconds=35)
        self.lane1.save()

        self.client.login(username="org", password=PWD)
        self.client.post(reverse("finish_heat_all_dns", args=[self.heat.id]))

        self.lane1.refresh_from_db()
        lane2.refresh_from_db()
        self.heat.refresh_from_db()
        self.assertFalse(self.lane1.dns)
        self.assertEqual(self.lane1.result_time, timedelta(seconds=35))
        self.assertTrue(lane2.dns)
        self.assertEqual(self.heat.status, Heat.Status.FINISHED)

    def test_all_dns_forbidden_for_coach(self):
        self.client.login(username="coach1", password=PWD)
        response = self.client.post(reverse("finish_heat_all_dns", args=[self.heat.id]))
        self.assertEqual(response.status_code, 403)

    def test_all_dns_on_finished_heat_changes_nothing(self):
        self.heat.status = Heat.Status.FINISHED
        self.heat.save()
        self.client.login(username="org", password=PWD)
        self.client.post(reverse("finish_heat_all_dns", args=[self.heat.id]))
        self.lane1.refresh_from_db()
        self.assertFalse(self.lane1.dns)


class MyResultsTest(BaseCompetitionTest):
    def setUp(self):
        super().setUp()
        self.user = make_user("ath", "athlete")
        self.athlete = Athlete.objects.create(
            first_name="Иван",
            last_name="Иванов",
            birth_year=2011,
            gender="male",
            team=Team.objects.create(name="T", city=""),
            coach=self.coach,
            user=self.user,
        )
        self.ae = AthleteEvent.objects.create(
            athlete=self.athlete,
            event=self.event_free,
            application=self.application,
        )
        self.heat = Heat.objects.create(event=self.event_free, number=1)
        HeatLane.objects.create(
            heat=self.heat,
            athlete_event=self.ae,
            lane=3,
            result_time=timedelta(seconds=33),
        )
        self.client.login(username="ath", password=PWD)

    def test_unfinished_heat_hidden(self):
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.context["my_results"], [])

    def test_finished_heat_shows_result_and_place(self):
        self.heat.status = Heat.Status.FINISHED
        self.heat.save()
        response = self.client.get(reverse("profile"))
        rows = response.context["my_results"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["place"], 1)
        self.assertEqual(rows[0]["time"], timedelta(seconds=33))

    def test_other_users_results_not_shown(self):
        self.athlete.user = None
        self.athlete.save()
        self.heat.status = Heat.Status.FINISHED
        self.heat.save()
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.context["my_results"], [])
