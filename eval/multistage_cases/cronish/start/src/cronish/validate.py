"""Checking an expression before it is saved or scheduled."""
from ._generated import MONTH_LENGTHS
from .errors import ScheduleError
from .expression import parse


def validate(text):
    """Messages describing what is wrong with `text`; empty when it is usable."""
    try:
        schedule = parse(text)
    except ScheduleError as error:
        return [str(error)]
    problem = _impossible_day(schedule)
    return [str(problem)] if problem else []


def _impossible_day(schedule):
    # Only when the weekday field is a star: otherwise the weekdays alone can still match.
    if schedule.day_star or not schedule.weekday_star:
        return None
    longest = max(MONTH_LENGTHS[month - 1] for month in schedule.months)
    if min(schedule.days) > longest:
        return ScheduleError("day", f"no selected month has a day {min(schedule.days)}")
    return None
