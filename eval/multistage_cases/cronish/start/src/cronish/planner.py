"""Finding the moments a schedule runs."""
from datetime import datetime, time, timedelta
from itertools import islice

from .errors import ScheduleError

DEFAULT_COUNT = 5
MAX_COUNT = 100
HORIZON_YEARS = 5
HORIZON = timedelta(days=round(365.25 * HORIZON_YEARS))


def weekday_number(day):
    """The number a schedule uses for the weekday of `day`; Sunday is 0."""
    return day.isoweekday() % 7


def day_matches(schedule, day):
    if day.month not in schedule.months:
        return False
    in_days = day.day in schedule.days
    in_weekdays = weekday_number(day) in schedule.weekdays
    # Cron's rule: when both day fields are restricted, a day matching either one runs.
    if schedule.day_star or schedule.weekday_star:
        return in_days and in_weekdays
    return in_days or in_weekdays


def next_runs(schedule, now, count=DEFAULT_COUNT):
    """The next `count` runs at or after `now`, earliest first."""
    if not 1 <= count <= MAX_COUNT:
        raise ScheduleError(None, f"count must be between 1 and {MAX_COUNT}")
    start = now.replace(second=0, microsecond=0)
    if start < now:
        start += timedelta(minutes=1)
    runs = list(islice(_forward(schedule, start), count))
    if not runs:
        raise ScheduleError(None, f"no run within {HORIZON_YEARS} years")
    return runs


def runs_between(schedule, start, end):
    """Every run from `start` up to, but not including, `end`."""
    first = start.replace(second=0, microsecond=0)
    if first < start:
        first += timedelta(minutes=1)
    runs = []
    for moment in _forward(schedule, first):
        if moment >= end:
            break
        runs.append(moment)
    return runs


def previous_run(schedule, now):
    """The latest run at or before `now`."""
    end = now.replace(second=0, microsecond=0)
    day, first = end.date(), end.date() - HORIZON
    while day >= first:
        if day_matches(schedule, day):
            for hour in reversed(schedule.hours):
                for minute in reversed(schedule.minutes):
                    moment = datetime.combine(day, time(hour, minute), tzinfo=now.tzinfo)
                    if moment <= end:
                        return moment
        day -= timedelta(days=1)
    raise ScheduleError(None, f"no run within {HORIZON_YEARS} years")


def _forward(schedule, start):
    day, last = start.date(), start.date() + HORIZON
    while day <= last:
        if day_matches(schedule, day):
            for hour in schedule.hours:
                for minute in schedule.minutes:
                    moment = datetime.combine(day, time(hour, minute), tzinfo=start.tzinfo)
                    if moment >= start:
                        yield moment
        day += timedelta(days=1)
