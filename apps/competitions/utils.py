import openpyxl
from datetime import timedelta
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation


def generate_application_template():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Заявка"

    headers = [
        "Фамилия",
        "Имя",
        "Год рождения",
        "Пол (М/Ж)",
        "Команда / Тренер",
        "Дистанция (м)",
        "Стиль",
        "Предварительное время (мм:сс.сс)",
        "ВК (да/нет)",
    ]

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(
        start_color="003366", end_color="003366", fill_type="solid"
    )
    header_alignment = Alignment(horizontal="center")

    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment

    column_widths = [20, 15, 15, 12, 25, 15, 20, 30, 12]
    for col, width in enumerate(column_widths, start=1):
        ws.column_dimensions[get_column_letter(col)].width = width

    gender_validation = DataValidation(
        type="list",
        formula1='"М,Ж"',
        allow_blank=False,
        showErrorMessage=True,
        errorTitle="Неверное значение",
        error="Введите М или Ж",
    )
    ws.add_data_validation(gender_validation)
    gender_validation.add("D2:D1000")

    stroke_validation = DataValidation(
        type="list",
        formula1='"кроль,спина,брасс,баттерфляй,комплекс"',
        allow_blank=False,
        showErrorMessage=True,
        errorTitle="Неверное значение",
        error="Выберите стиль из списка",
    )
    ws.add_data_validation(stroke_validation)
    stroke_validation.add("G2:G1000")

    okc_validation = DataValidation(
        type="list",
        formula1='"нет,да"',
        allow_blank=False,
        showErrorMessage=True,
        errorTitle="Неверное значение",
        error="Выберите да или нет",
    )
    ws.add_data_validation(okc_validation)
    okc_validation.add("I2:I1000")

    example_row = [
        "Иванов",
        "Иван",
        2013,
        "М",
        "iSwim Астана / ФИ тренера",
        50,
        "кроль",
        "00:32.45",
        "нет",
    ]
    for col, value in enumerate(example_row, start=1):
        cell = ws.cell(row=2, column=col, value=value)
        cell.font = Font(italic=True, color="999999")

    return wb


def _parse_time(value):
    """'мм:сс.сс' -> timedelta. Бросает ValueError при неверном формате."""
    parts = str(value).strip().replace(",", ".").split(":")
    if len(parts) != 2:
        raise ValueError("формат мм:сс.сс")
    minutes = int(parts[0])
    seconds = float(parts[1])
    return timedelta(milliseconds=round((minutes * 60 + seconds) * 1000))


def _get_or_create_athlete(
    first_name, last_name, birth_year, gender, team, application
):
    """
    Ключ: ФИО + год рождения (без тренера и команды).
    Возвращает (athlete, status), где status:
      'created'   - новый спортсмен
      'existing'  - найден один, использован
      'ambiguous' - найдено несколько, ничего не склеиваем
    """
    from apps.teams.models import Athlete

    matches = list(
        Athlete.objects.filter(
            first_name__iexact=first_name,
            last_name__iexact=last_name,
            birth_year=birth_year,
        )
    )

    if len(matches) == 1:
        athlete = matches[0]
        # Привязка к человеку, а не к тренеру: обновляем команду и тренера
        athlete.team = team
        athlete.coach = application.coach
        athlete.application = application
        athlete.save(update_fields=["team", "coach", "application", "updated_at"])
        return athlete, "existing"

    if len(matches) > 1:
        return None, "ambiguous"

    athlete = Athlete.objects.create(
        first_name=first_name,
        last_name=last_name,
        birth_year=birth_year,
        gender=gender,
        team=team,
        coach=application.coach,
        application=application,
    )
    return athlete, "created"


def parse_application_excel(file, application):
    from apps.competitions.models import Event, AthleteEvent
    from apps.teams.models import Team

    wb = openpyxl.load_workbook(file)
    ws = wb.active

    stroke_map = {
        "кроль": "freestyle",
        "спина": "backstroke",
        "брасс": "breaststroke",
        "баттерфляй": "butterfly",
        "комплекс": "medley",
    }
    gender_map = {"м": "male", "ж": "female"}

    errors = []
    skipped = []
    athletes_created = []
    stats = {"new": 0, "existing": 0, "with_profile": 0, "ambiguous": 0}

    for row_num, row in enumerate(ws.iter_rows(min_row=3, values_only=True), start=3):
        # Строка считается пустой, если нет ни одного значения, кроме колонки ВК
        if not any(row[:8]):
            continue

        row = tuple(row) + (None,) * (9 - len(row))
        (
            last_name,
            first_name,
            birth_year,
            gender,
            team_name,
            distance,
            stroke,
            prelim_time,
            out_of_competition,
        ) = row[:9]

        # Пустой ВК считаем как «нет»
        if not out_of_competition:
            out_of_competition = "нет"

        if not all(
            [last_name, first_name, birth_year, gender, team_name, distance, stroke]
        ):
            errors.append(f"Строка {row_num}: не все обязательные поля заполнены")
            continue

        gender_normalized = gender_map.get(str(gender).strip().lower())
        if not gender_normalized:
            errors.append(
                f'Строка {row_num}: неверный пол "{gender}" — используйте М или Ж'
            )
            continue

        stroke_normalized = stroke_map.get(str(stroke).strip().lower())
        if not stroke_normalized:
            errors.append(f'Строка {row_num}: неверный стиль "{stroke}"')
            continue

        try:
            birth_year = int(birth_year)
            distance = int(distance)
        except (ValueError, TypeError):
            errors.append(
                f"Строка {row_num}: год рождения и дистанция должны быть числами"
            )
            continue

        try:
            event = Event.objects.get(
                competition=application.competition,
                gender=gender_normalized,
                stroke=stroke_normalized,
                distance=distance,
                birth_year_from__lte=birth_year,
                birth_year_to__gte=birth_year,
            )
        except Event.DoesNotExist:
            errors.append(
                f"Строка {row_num}: нет категории для {gender} {birth_year} {distance}м {stroke}"
            )
            continue
        except Event.MultipleObjectsReturned:
            errors.append(
                f"Строка {row_num}: найдено несколько подходящих категорий, обратитесь к организатору"
            )
            continue

        preliminary_time = None
        if prelim_time:
            try:
                preliminary_time = _parse_time(prelim_time)
            except Exception:
                errors.append(
                    f'Строка {row_num}: неверный формат времени "{prelim_time}" — используйте мм:сс.сс'
                )
                continue

        first_name = str(first_name).strip()
        last_name = str(last_name).strip()

        team, _ = Team.objects.get_or_create(
            name=str(team_name).strip(),
            defaults={"city": "", "coach": application.coach},
        )

        athlete, status = _get_or_create_athlete(
            first_name, last_name, birth_year, gender_normalized, team, application
        )

        if status == "ambiguous":
            stats["ambiguous"] += 1
            errors.append(
                f"Строка {row_num}: найдено несколько спортсменов "
                f"{last_name} {first_name} {birth_year}, обратитесь к организатору"
            )
            continue

        # Защита от дублей: этот спортсмен уже заявлен в категорию
        if AthleteEvent.objects.filter(athlete=athlete, event=event).exists():
            skipped.append(
                f"Строка {row_num}: {last_name} {first_name} {birth_year} "
                f"уже заявлен в категорию {event}"
            )
            continue

        AthleteEvent.objects.create(
            athlete=athlete,
            event=event,
            application=application,
            preliminary_time=preliminary_time,
            is_out_of_competition=str(out_of_competition).strip().lower()
            in ("да", "yes", "1", "true"),
        )

        if status == "created":
            stats["new"] += 1
        else:
            stats["existing"] += 1
            if getattr(athlete, "user_id", None):
                stats["with_profile"] += 1

        athletes_created.append(f"{last_name} {first_name}")

    unique_athletes = sorted(set(athletes_created))
    return {
        "success": len(athletes_created),
        "athletes_count": len(unique_athletes),
        "errors": errors,
        "skipped": skipped,
        "athletes": unique_athletes,
        "stats": stats,
    }
