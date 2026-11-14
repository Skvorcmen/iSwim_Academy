from datetime import date, timedelta
from django.test import TestCase
from apps.competitions.models import (
    Application,
    AthleteEvent,
    Competition,
    Event,
    Heat,
    HeatLane,
)
from apps.competitions.services import (
    form_heats_for_competition,
    get_snake_lane_order,
    split_into_heats,
)
from apps.teams.models import Athlete, Team
from apps.users.models import User


class SnakeAndSplitTest(TestCase):

    def test_snake_order_6(self):
        self.assertEqual(get_snake_lane_order(6), [3, 4, 2, 5, 1, 6])

    def test_snake_order_8(self):
        self.assertEqual(get_snake_lane_order(8), [4, 5, 3, 6, 2, 7, 1, 8])

    def test_snake_order_6_lanes_from_second(self):
        self.assertEqual(get_snake_lane_order(6, first_lane=2), [4, 5, 3, 6, 2, 7])

    def test_split_sizes(self):
        self.assertEqual(split_into_heats(5, 6), [5])
        self.assertEqual(split_into_heats(6, 6), [6])
        self.assertEqual(split_into_heats(7, 6), [3, 4])
        self.assertEqual(sorted(split_into_heats(14, 6)), [4, 5, 5])


class HeatFormationTest(TestCase):
    def setUp(self):
        self.coach = User.objects.create_user(username="c", password="x", role="coach")
        self.comp = Competition.objects.create(
            name="K", date=date(2026, 12, 1), location="A", lanes_count=6
        )
        self.event = self._event("freestyle", 1)
        self.app = Application.objects.create(competition=self.comp, coach=self.coach)
        self.team = Team.objects.create(name="T", city="")
        self.counter = 0

    def _event(self, stroke, order):
        return Event.objects.create(
            competition=self.comp,
            gender="male",
            birth_year_from=2010,
            birth_year_to=2012,
            distance=50,
            stroke=stroke,
            order=order,
        )

    def add(self, prelim_seconds, event=None, **kw):
        self.counter += 1
        ath = Athlete.objects.create(
            first_name=f"N{self.counter}",
            last_name=f"L{self.counter}",
            birth_year=2011,
            gender="male",
            team=self.team,
            coach=self.coach,
        )
        prelim = None if prelim_seconds is None else timedelta(seconds=prelim_seconds)
        return AthleteEvent.objects.create(
            athlete=ath,
            event=event or self.event,
            application=self.app,
            preliminary_time=prelim,
            **kw,
        )

    def test_working_lanes_2_to_7(self):
        self.comp.first_lane = 2
        self.comp.save()
        for i in range(6):
            self.add(30 + i)
        form_heats_for_competition(self.comp)
        lanes = sorted(HeatLane.objects.values_list("lane", flat=True))
        self.assertEqual(lanes, [2, 3, 4, 5, 6, 7])
        fastest = HeatLane.objects.get(
            athlete_event__preliminary_time=timedelta(seconds=30)
        )
        self.assertEqual(fastest.lane, 4)

    def heats(self, event=None):
        return list(Heat.objects.filter(event=event or self.event).order_by("number"))

    def athletes_in(self, heat):
        return [hl.athlete_event for hl in heat.heatlane_set.all()]

    # --- заплывы с временем ---

    def test_slowest_heat_first_fastest_in_center_lane(self):
        aes = [self.add(30 + i) for i in range(8)]  # 30..37 с
        form_heats_for_competition(self.comp)
        heats = self.heats()
        self.assertEqual(len(heats), 2)
        slow = [ae.preliminary_time for ae in self.athletes_in(heats[0])]
        fast = [ae.preliminary_time for ae in self.athletes_in(heats[1])]
        self.assertGreaterEqual(min(slow), max(fast))
        fastest = HeatLane.objects.get(athlete_event=aes[0])
        self.assertEqual(fastest.lane, get_snake_lane_order(6)[0])

    def test_lanes_unique_within_heat_and_all_athletes_placed(self):
        for i in range(14):
            self.add(30 + i)
        form_heats_for_competition(self.comp)
        self.assertEqual(HeatLane.objects.count(), 14)
        for heat in self.heats():
            lanes = list(heat.heatlane_set.values_list("lane", flat=True))
            self.assertEqual(len(lanes), len(set(lanes)))
            self.assertLessEqual(len(lanes), 6)

    # --- FINA: без предвремени отдельным первым заплывом ---

    def test_unseeded_swim_separate_first_heat(self):
        for i in range(4):
            self.add(30 + i)
        for _ in range(3):
            self.add(None)
        form_heats_for_competition(self.comp)
        heats = self.heats()
        self.assertEqual(len(heats), 2)
        self.assertTrue(
            all(ae.preliminary_time is None for ae in self.athletes_in(heats[0]))
        )
        self.assertTrue(
            all(ae.preliminary_time is not None for ae in self.athletes_in(heats[1]))
        )

    def test_many_unseeded_none_lost(self):
        self.add(30)
        for _ in range(14):
            self.add(None)
        form_heats_for_competition(self.comp)
        self.assertEqual(HeatLane.objects.count(), 15)
        for heat in self.heats():
            self.assertLessEqual(heat.heatlane_set.count(), 6)

    def test_only_unseeded_single_heat(self):
        for _ in range(4):
            self.add(None)
        form_heats_for_competition(self.comp)
        heats = self.heats()
        self.assertEqual(len(heats), 1)
        self.assertEqual(heats[0].heatlane_set.count(), 4)

    # --- общее ---

    def test_withdrawn_excluded(self):
        self.add(30)
        self.add(31, participation_status=AthleteEvent.ParticipationStatus.WITHDRAWN)
        form_heats_for_competition(self.comp)
        self.assertEqual(HeatLane.objects.count(), 1)

    def test_numbering_continuous_across_events(self):
        ev2 = self._event("backstroke", 2)
        for i in range(7):
            self.add(30 + i)
        for i in range(3):
            self.add(40 + i, event=ev2)
        form_heats_for_competition(self.comp)
        numbers = list(
            Heat.objects.filter(event__competition=self.comp)
            .order_by("number")
            .values_list("number", flat=True)
        )
        self.assertEqual(numbers, list(range(1, len(numbers) + 1)))

    def test_repeat_formation_ignored(self):
        for i in range(5):
            self.add(30 + i)
        form_heats_for_competition(self.comp)
        count = Heat.objects.count()
        form_heats_for_competition(self.comp)
        self.assertEqual(Heat.objects.count(), count)

    def test_competition_goes_in_progress(self):
        self.add(30)
        form_heats_for_competition(self.comp)
        self.comp.refresh_from_db()
        self.assertEqual(self.comp.status, Competition.Status.IN_PROGRESS)
