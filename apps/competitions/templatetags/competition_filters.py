from django import template

register = template.Library()


@register.filter
def format_time(duration):
    """Форматирует timedelta в мм:сс.сс — возвращает тире если нет значения."""
    if not duration:
        return '—'
    total_seconds = int(duration.total_seconds())
    milliseconds = duration.microseconds // 10000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f'{minutes:02d}:{seconds:02d}.{milliseconds:02d}'


@register.filter
def format_time_input(duration):
    """Форматирует timedelta для поля ввода — пустая строка если нет значения."""
    if not duration:
        return ''
    total_seconds = int(duration.total_seconds())
    milliseconds = duration.microseconds // 10000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f'{minutes:02d}:{seconds:02d}.{milliseconds:02d}'