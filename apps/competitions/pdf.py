from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import os

DARK_BLUE = colors.HexColor("#003366")
LIGHT_BLUE = colors.HexColor("#0066CC")


def register_fonts():
    regular = "/Library/Fonts/Arial Unicode.ttf"
    bold = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

    if os.path.exists(regular):
        pdfmetrics.registerFont(TTFont("CustomFont", regular))
    if os.path.exists(bold):
        pdfmetrics.registerFont(TTFont("CustomFont-Bold", bold))

    return "CustomFont"


def format_time(duration):
    if not duration:
        return "—"
    total_seconds = int(duration.total_seconds())
    milliseconds = duration.microseconds // 10000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}.{milliseconds:02d}"


def generate_event_results_pdf(event, results):
    buffer = BytesIO()
    font_name = register_fonts()
    font_bold = "CustomFont-Bold"

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=16,
        textColor=DARK_BLUE,
        spaceAfter=6,
        fontName=font_bold,
    )

    subtitle_style = ParagraphStyle(
        "CustomSubtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.grey,
        spaceAfter=4,
        fontName=font_name,
    )

    elements = []

    elements.append(Paragraph("iSwim — Протокол результатов", title_style))
    elements.append(Paragraph(str(event), subtitle_style))
    elements.append(
        Paragraph(
            f"Соревнование: {event.competition.name} | Дата: {event.competition.date}",
            subtitle_style,
        )
    )
    elements.append(Spacer(1, 0.5 * cm))

    table_data = [
        ["Место", "Спортсмен", "Команда", "Год", "Время / Статус", "Заплыв", "Дор."]
    ]

    for result in results:
        place_str = str(result["place"]) if result["place"] else "—"
        time_str = result["status"] if result["status"] else format_time(result["time"])
        athlete = result["athlete"]

        table_data.append(
            [
                place_str,
                f"{athlete.last_name} {athlete.first_name}",
                str(athlete.team),
                str(athlete.birth_year),
                time_str,
                str(result["heat_number"]),
                str(result["lane"]),
            ]
        )

    col_widths = [2 * cm, 5.5 * cm, 4.5 * cm, 1.8 * cm, 3 * cm, 1.8 * cm, 1.5 * cm]

    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    table_style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), font_bold),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [colors.white, colors.HexColor("#f5f8ff")],
            ),
            ("FONTNAME", (0, 1), (-1, -1), font_name),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]
    )

    for i, result in enumerate(results, start=1):
        if result["status"]:
            table_style.add("TEXTCOLOR", (4, i), (4, i), colors.red)

    table.setStyle(table_style)
    elements.append(table)

    elements.append(Spacer(1, 1 * cm))
    elements.append(
        Paragraph("Документ сформирован автоматически системой iSwim", subtitle_style)
    )

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_competition_results_pdf(competition):
    """
    Генерирует полный протокол всего соревнования.
    Все категории в одном PDF по порядку.
    """
    from apps.competitions.models import Event
    from apps.competitions.services import calculate_results_for_event

    buffer = BytesIO()
    font_name = register_fonts()
    font_bold = "CustomFont-Bold"

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=18,
        textColor=DARK_BLUE,
        spaceAfter=6,
        fontName=font_bold,
    )

    category_style = ParagraphStyle(
        "CategoryTitle",
        parent=styles["Normal"],
        fontSize=13,
        textColor=DARK_BLUE,
        spaceAfter=4,
        spaceBefore=16,
        fontName=font_bold,
    )

    subtitle_style = ParagraphStyle(
        "CustomSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=4,
        fontName=font_name,
    )

    elements = []

    # Шапка всего протокола
    elements.append(Paragraph("iSwim — Итоговый протокол", title_style))
    elements.append(Paragraph(competition.name, category_style))
    elements.append(
        Paragraph(
            f"Дата: {competition.date} | Место: {competition.location}", subtitle_style
        )
    )
    elements.append(Spacer(1, 0.5 * cm))

    events = Event.objects.filter(competition=competition).order_by("order")

    for event in events:
        results = calculate_results_for_event(event)
        if not results:
            continue

        elements.append(Paragraph(str(event), category_style))

        table_data = [
            ["Место", "Спортсмен", "Команда", "Год", "Время / Статус", "Заплыв", "Дор."]
        ]

        for result in results:
            place_str = str(result["place"]) if result["place"] else "—"
            time_str = (
                result["status"] if result["status"] else format_time(result["time"])
            )
            athlete = result["athlete"]

            table_data.append(
                [
                    place_str,
                    f"{athlete.last_name} {athlete.first_name}",
                    str(athlete.team),
                    str(athlete.birth_year),
                    time_str,
                    str(result["heat_number"]),
                    str(result["lane"]),
                ]
            )

        col_widths = [2 * cm, 5.5 * cm, 4.5 * cm, 1.8 * cm, 3 * cm, 1.8 * cm, 1.5 * cm]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)

        table_style = TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), font_bold),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f5f8ff")],
                ),
                ("FONTNAME", (0, 1), (-1, -1), font_name),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]
        )

        for i, result in enumerate(results, start=1):
            if result["status"]:
                table_style.add("TEXTCOLOR", (4, i), (4, i), colors.red)

        table.setStyle(table_style)
        elements.append(table)
        elements.append(Spacer(1, 0.5 * cm))

    elements.append(Spacer(1, 1 * cm))
    elements.append(
        Paragraph("Документ сформирован автоматически системой iSwim", subtitle_style)
    )

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_start_protocol_pdf(competition):
    """
    Генерирует стартовый протокол — список всех заплывов с дорожками.
    """
    from apps.competitions.models import Heat, HeatLane

    buffer = BytesIO()
    font_name = register_fonts()
    font_bold = "CustomFont-Bold"

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=18,
        textColor=DARK_BLUE,
        spaceAfter=6,
        fontName=font_bold,
    )

    category_style = ParagraphStyle(
        "CategoryTitle",
        parent=styles["Normal"],
        fontSize=12,
        textColor=DARK_BLUE,
        spaceAfter=4,
        spaceBefore=12,
        fontName=font_bold,
    )

    subtitle_style = ParagraphStyle(
        "CustomSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=4,
        fontName=font_name,
    )

    elements = []

    elements.append(Paragraph("iSwim — Стартовый протокол", title_style))
    elements.append(Paragraph(competition.name, category_style))
    elements.append(
        Paragraph(
            f"Дата: {competition.date} | Место: {competition.location}", subtitle_style
        )
    )
    elements.append(Spacer(1, 0.5 * cm))

    heats = (
        Heat.objects.filter(event__competition=competition)
        .select_related("event")
        .order_by("number")
    )

    for heat in heats:
        elements.append(
            Paragraph(f"Заплыв {heat.number} — {heat.event}", category_style)
        )

        lanes = (
            HeatLane.objects.filter(heat=heat)
            .select_related("athlete_event__athlete__team")
            .order_by("lane")
        )

        table_data = [["Дор.", "Спортсмен", "Команда", "Год", "Предвремя", "ВК"]]

        for lane in lanes:
            athlete = lane.athlete_event.athlete
            prelim = format_time(lane.athlete_event.preliminary_time)
            is_okc = "ВК" if lane.athlete_event.is_out_of_competition else ""

            table_data.append(
                [
                    str(lane.lane),
                    f"{athlete.last_name} {athlete.first_name}",
                    str(athlete.team),
                    str(athlete.birth_year),
                    prelim,
                    is_okc,
                ]
            )

        col_widths = [1.5 * cm, 5.5 * cm, 4.5 * cm, 1.8 * cm, 3 * cm, 1.5 * cm]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)

        table_style = TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), font_bold),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f5f8ff")],
                ),
                ("FONTNAME", (0, 1), (-1, -1), font_name),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]
        )

        for i, lane in enumerate(lanes, start=1):
            if lane.athlete_event.is_out_of_competition:
                table_style.add("TEXTCOLOR", (5, i), (5, i), colors.red)

        table.setStyle(table_style)
        elements.append(table)
        elements.append(Spacer(1, 0.3 * cm))

    elements.append(Spacer(1, 1 * cm))
    elements.append(
        Paragraph("Документ сформирован автоматически системой iSwim", subtitle_style)
    )

    doc.build(elements)
    buffer.seek(0)
    return buffer
