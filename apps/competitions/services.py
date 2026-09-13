import random
from apps.competitions.models import Event, AthleteEvent, Heat, HeatLane
from django.db import models


def get_snake_lane_order(lanes_count):
    """
    Возвращает порядок дорожек от центра к краям.
    Для 6 дорожек: [4, 3, 5, 2, 6, 1]
    Для 8 дорожек: [4, 5, 3, 6, 2, 7, 1, 8]
    """
    center = lanes_count // 2
    order = []
    left = center
    right = center + 1

    for i in range(lanes_count):
        if i % 2 == 0:
            order.append(right)
            right += 1
        else:
            order.append(left)
            left -= 1

    return order


def split_into_heats(athletes_count, lanes_count):
    """
    Делит количество спортсменов на заплывы.
    Минимум 3 человека в заплыве (кроме случаев когда всего меньше 3).
    Возвращает список размеров заплывов, например [4, 5, 5].
    """
    if athletes_count <= lanes_count:
        return [athletes_count]

    heats_count = -(-athletes_count // lanes_count)  # округление вверх

    base = athletes_count // heats_count
    remainder = athletes_count % heats_count

    heat_sizes = [base] * heats_count
    for i in range(remainder):
        heat_sizes[-(i + 1)] += 1

    return heat_sizes


def form_heats_for_event(event, starting_heat_number=1):
    """
    Формирует заплывы для одной категории (Event).
    Спортсмены без времени попадают в первый (медленный) заплыв.
    Возвращает номер следующего свободного заплыва.
    """
    competition = event.competition
    lanes_count = competition.lanes_count

    athlete_events = AthleteEvent.objects.filter(
        event=event,
        participation_status=AthleteEvent.ParticipationStatus.ACTIVE,
    )

    with_time = list(athlete_events.filter(preliminary_time__isnull=False))
    without_time = list(athlete_events.filter(preliminary_time__isnull=True))

    # Сортируем от медленных к быстрым
    with_time.sort(key=lambda ae: ae.preliminary_time, reverse=True)

    # Без времени — жеребьёвка между собой
    random.shuffle(without_time)

    total_with_time = len(with_time)
    total_without_time = len(without_time)
    total = total_with_time + total_without_time

    if total == 0:
        return starting_heat_number

    lane_order = get_snake_lane_order(lanes_count)
    heat_number = starting_heat_number

    # Шаг 1 — формируем заплывы только из спортсменов С временем
    if total_with_time > 0:
        heat_sizes = split_into_heats(total_with_time, lanes_count)
        index = 0

        for size in heat_sizes:
            heat_athletes = with_time[index : index + size]
            index += size

            heat = Heat.objects.create(event=event, number=heat_number)
            lanes_for_this_heat = lane_order[:size]
            reversed_lanes = list(reversed(lanes_for_this_heat))

            for athlete_event, lane in zip(heat_athletes, reversed_lanes):
                HeatLane.objects.create(
                    heat=heat,
                    athlete_event=athlete_event,
                    lane=lane,
                )

            heat_number += 1

    # Шаг 2 — спортсменов БЕЗ времени добавляем в первый заплыв категории
    # Если первый заплыв ещё не заполнен — добираем туда
    # Если уже полный — создаём новый первый заплыв (вставляем перед остальными)
    if total_without_time > 0:
        first_heat = Heat.objects.filter(
            event=event, number=starting_heat_number
        ).first()

        if first_heat:
            current_count = first_heat.heatlane_set.count()
            free_lanes = lanes_count - current_count

            # Сколько можно добавить в существующий первый заплыв
            can_add = min(free_lanes, total_without_time)
            to_add_first = without_time[:can_add]
            remaining = without_time[can_add:]

            # Добавляем в первый заплыв на оставшиеся дорожки
            used_lanes = set(first_heat.heatlane_set.values_list("lane", flat=True))
            available_lanes = [l for l in lane_order if l not in used_lanes]

            for athlete_event, lane in zip(to_add_first, available_lanes):
                HeatLane.objects.create(
                    heat=first_heat,
                    athlete_event=athlete_event,
                    lane=lane,
                )

            # Если остались — создаём дополнительный заплыв перед первым
            # Сдвигаем нумерацию всех существующих заплывов на 1
            if remaining:
                Heat.objects.filter(
                    event=event, number__gte=starting_heat_number
                ).update(number=models.F("number") + 1)

                new_first_heat = Heat.objects.create(
                    event=event,
                    number=starting_heat_number,
                )

                lanes_for_extra = lane_order[: len(remaining)]

                for athlete_event, lane in zip(remaining, lanes_for_extra):
                    HeatLane.objects.create(
                        heat=new_first_heat,
                        athlete_event=athlete_event,
                        lane=lane,
                    )

                heat_number += 1

        else:
            # Нет заплывов с временем — все без времени, один заплыв
            heat = Heat.objects.create(event=event, number=heat_number)
            lanes_for_this_heat = lane_order[:total_without_time]

            for athlete_event, lane in zip(without_time, lanes_for_this_heat):
                HeatLane.objects.create(
                    heat=heat,
                    athlete_event=athlete_event,
                    lane=lane,
                )

            heat_number += 1

    event.status = Event.Status.SEEDED
    event.save()

    return heat_number


def calculate_results_for_event(event):
    """
    Подсчитывает места для всех спортсменов категории (Event)
    после того как все заплывы этой категории завершены.
    Возвращает список словарей, отсортированный: сначала места по времени,
    затем DNS/DNF/DSQ без места.
    """
    from apps.competitions.models import Heat, HeatLane

    heats = Heat.objects.filter(event=event)

    if heats.filter(status=Heat.Status.PENDING).exists():
        return None

    all_lanes = HeatLane.objects.filter(heat__event=event).select_related(
        "athlete_event__athlete", "heat"
    )

    finished_lanes = [
        l for l in all_lanes if l.result_time and not (l.dns or l.dnf or l.dsq)
    ]
    non_finished_lanes = [l for l in all_lanes if l.dns or l.dnf or l.dsq]

    sorted_lanes = sorted(finished_lanes, key=lambda l: l.result_time)

    results = []
    current_place = 1

    for i, lane in enumerate(sorted_lanes):
        if i > 0 and lane.result_time == sorted_lanes[i - 1].result_time:
            place = results[-1]["place"]
        else:
            place = current_place

        is_okc = lane.athlete_event.is_out_of_competition

        results.append(
            {
                "place": None if is_okc else place,
                "athlete": lane.athlete_event.athlete,
                "time": lane.result_time,
                "heat_number": lane.heat.number,
                "lane": lane.lane,
                "status": "ВК" if is_okc else None,
            }
        )

        if not is_okc:
            current_place += 1

    # Добавляем DNS/DNF/DSQ без места, в конец протокола
    for lane in non_finished_lanes:
        if lane.dns:
            status = "DNS"
        elif lane.dnf:
            status = "DNF"
        elif lane.dsq:
            status = "DSQ"
        else:
            status = None

        results.append(
            {
                "place": None,
                "athlete": lane.athlete_event.athlete,
                "time": None,
                "heat_number": lane.heat.number,
                "lane": lane.lane,
                "status": status,
            }
        )

    event.status = event.Status.FINISHED
    event.save()

    return results


def form_heats_for_competition(competition):
    # Защита от повторного формирования
    if Heat.objects.filter(event__competition=competition).exists():
        return
    """
    Формирует заплывы для всех категорий соревнования по порядку.
    """
    events = Event.objects.filter(competition=competition).order_by("order")

    heat_number = 1
    for event in events:
        heat_number = form_heats_for_event(event, starting_heat_number=heat_number)

    competition.status = competition.Status.IN_PROGRESS
    competition.save()
