import random
from apps.competitions.models import (
    Competition,
    Event,
    AthleteEvent,
    Heat,
    HeatLane,
)


def get_snake_lane_order(lanes_count, first_lane=1):
    """
    Порядок дорожек по FINA: самый быстрый в центре, дальше вправо и влево.
    6 дорожек: 3,4,2,5,1,6. 8 дорожек: 4,5,3,6,2,7,1,8.
    first_lane сдвигает нумерацию (для 6 дорожек со 2-й: 4,5,3,6,2,7).
    """
    center = (lanes_count + 1) // 2
    order = [center]
    step = 1
    while len(order) < lanes_count:
        if center + step <= lanes_count:
            order.append(center + step)
        if center - step >= 1 and len(order) < lanes_count:
            order.append(center - step)
        step += 1
    return [first_lane + p - 1 for p in order]


def split_into_heats(athletes_count, lanes_count):
    """
    Делит количество спортсменов на заплывы.
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


def _create_heat(event, number, athlete_events, lanes):
    heat = Heat.objects.create(event=event, number=number)
    for athlete_event, lane in zip(athlete_events, lanes):
        HeatLane.objects.create(heat=heat, athlete_event=athlete_event, lane=lane)
    return heat


def form_heats_for_event(event, starting_heat_number=1):
    """
    Формирует заплывы для одной категории.
    Порядок по правилам FINA:
      1. Спортсмены без предвремени: отдельные первые заплывы, жеребьёвка дорожек.
      2. Спортсмены с временем: от медленных к быстрым, самый быстрый
         в центральной дорожке.
    Возвращает номер следующего свободного заплыва.
    """
    lanes_count = event.competition.lanes_count

    athlete_events = AthleteEvent.objects.filter(
        event=event,
        participation_status=AthleteEvent.ParticipationStatus.ACTIVE,
    )
    with_time = list(athlete_events.filter(preliminary_time__isnull=False))
    without_time = list(athlete_events.filter(preliminary_time__isnull=True))

    if not with_time and not without_time:
        return starting_heat_number

    lane_order = get_snake_lane_order(lanes_count, event.competition.first_lane)
    heat_number = starting_heat_number

    # 1. Без предвремени: жеребьёвка состава и дорожек
    if without_time:
        random.shuffle(without_time)
        index = 0
        for size in split_into_heats(len(without_time), lanes_count):
            chunk = without_time[index : index + size]
            index += size
            lanes = lane_order[:size]
            random.shuffle(lanes)
            _create_heat(event, heat_number, chunk, lanes)
            heat_number += 1

    # 2. С предвременем: от медленных к быстрым
    if with_time:
        with_time.sort(key=lambda ae: ae.preliminary_time, reverse=True)
        index = 0
        for size in split_into_heats(len(with_time), lanes_count):
            chunk = with_time[index : index + size]
            index += size
            lanes = list(reversed(lane_order[:size]))
            _create_heat(event, heat_number, chunk, lanes)
            heat_number += 1

    event.status = Event.Status.SEEDED
    event.save()
    return heat_number


def calculate_results_for_event(event):
    """
    Подсчитывает места для всех спортсменов категории после того,
    как все заплывы категории начаты/завершены (нет заплывов «Ожидает»).
    Только читает данные, статусы не меняет.
    Возвращает список словарей: сначала места по времени,
    затем DNS/DNF/DSQ без места.
    """
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

    # DNS/DNF/DSQ без места, в конец протокола
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

    return results


def update_event_status_if_finished(event):
    """Ставит категории статус «Завершено», когда все её заплывы завершены."""
    heats = Heat.objects.filter(event=event)
    if heats.exists() and not heats.exclude(status=Heat.Status.FINISHED).exists():
        if event.status != Event.Status.FINISHED:
            event.status = Event.Status.FINISHED
            event.save(update_fields=["status", "updated_at"])


def form_heats_for_competition(competition):
    """
    Формирует заплывы для всех категорий соревнования по порядку.
    """
    # Защита от повторного формирования
    if Heat.objects.filter(event__competition=competition).exists():
        return

    events = Event.objects.filter(competition=competition).order_by("order")

    heat_number = 1
    for event in events:
        heat_number = form_heats_for_event(event, starting_heat_number=heat_number)

    competition.status = Competition.Status.IN_PROGRESS
    competition.save()
