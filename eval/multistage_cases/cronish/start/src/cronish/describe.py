"""Plain-English descriptions of schedules."""
from ._generated import DAY_TITLES, MONTH_TITLES
from .fields import DAY, HOUR, MINUTE, MONTH, WEEKDAY
from .formatting import clock, join_words

# Up to this many hour-and-minute combinations are spelled out as times of day.
EXACT_TIMES = 4


def describe(schedule):
    parts = [_time(schedule), _days(schedule)]
    if len(schedule.months) < MONTH.size:
        parts.append("in " + join_words(MONTH_TITLES[month - 1] for month in schedule.months))
    return ", ".join(parts)


def _time(schedule):
    minutes, hours = schedule.minutes, schedule.hours
    every_minute, every_hour = len(minutes) == MINUTE.size, len(hours) == HOUR.size
    if every_minute and every_hour:
        return "every minute"
    if len(minutes) * len(hours) <= EXACT_TIMES:
        return "at " + join_words(clock(hour, minute) for hour in hours for minute in minutes)
    if every_minute:
        return "every minute during " + _numbered("hour", hours)
    if every_hour:
        return f"at {_numbered('minute', minutes)} past every hour"
    return f"at {_numbered('minute', minutes)} past {_numbered('hour', hours)}"


def _days(schedule):
    every_day = len(schedule.days) == DAY.size
    every_weekday = len(schedule.weekdays) == WEEKDAY.size
    weekdays = "on " + join_words(DAY_TITLES[number] for number in schedule.weekdays)
    days = f"on {_numbered('day', schedule.days)} of the month"
    if every_day and every_weekday:
        return "every day"
    if every_day:
        return weekdays
    if every_weekday:
        return days
    joiner = " and " if schedule.day_star or schedule.weekday_star else " or "
    return days + joiner + weekdays


def _numbered(unit, values):
    label = unit if len(values) == 1 else unit + "s"
    return f"{label} {join_words(str(value) for value in values)}"
