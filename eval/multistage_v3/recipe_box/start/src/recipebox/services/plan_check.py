"""Gentle warnings about a meal plan: repeats, gaps and long cooking on weekdays."""
from dataclasses import dataclass

from ..core.plan import DAYS

WEEKDAYS = DAYS[:5]
# A weekday dinner taking longer than this gets a warning.
WEEKDAY_MINUTES = 60


@dataclass(frozen=True)
class PlanWarning:
    day: str
    message: str


def _repeats(plan):
    found = []
    previous = set()
    for day in DAYS:
        titles = {entry.recipe.title for entry in plan.on(day)}
        for title in sorted(titles & previous):
            found.append(PlanWarning(day, f"{title} again, as the day before"))
        previous = titles
    return found


def _gaps(plan):
    planned = plan.days()
    if not planned:
        return []
    first, last = DAYS.index(planned[0]), DAYS.index(planned[-1])
    return [PlanWarning(day, "nothing planned") for day in DAYS[first:last + 1] if day not in planned]


def _long_weekdays(plan):
    found = []
    for day in WEEKDAYS:
        for entry in plan.on(day):
            minutes = entry.recipe.minutes
            if entry.meal == "dinner" and minutes is not None and minutes > WEEKDAY_MINUTES:
                found.append(PlanWarning(day, f"{entry.recipe.title} takes {minutes} min on a weekday"))
    return found


def check_plan(plan):
    """Warnings in day order; an empty list means nothing to point out."""
    warnings = _repeats(plan) + _gaps(plan) + _long_weekdays(plan)
    return sorted(warnings, key=lambda warning: DAYS.index(warning.day))
