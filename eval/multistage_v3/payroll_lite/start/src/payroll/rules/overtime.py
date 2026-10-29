"""Sorting one employee's hours for a period into what each is paid as."""
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from payroll._generated import HOLIDAYS

NO_HOURS = Decimal("0.00")


@dataclass(frozen=True)
class Hours:
    ordinary: Decimal = NO_HOURS
    overtime: Decimal = NO_HOURS
    holiday: Decimal = NO_HOURS
    sick: Decimal = NO_HOURS
    # days with any work on them, which is what per-shift allowances count
    shifts: int = 0


def split_hours(entries, settings):
    """Work on a public holiday is all holiday hours; otherwise a day's work beyond the
    daily threshold is overtime. Sick hours are kept apart and never become overtime."""
    worked = defaultdict(Decimal)
    sick = NO_HOURS
    for entry in entries:
        if entry.kind == "sick":
            sick += entry.hours
        else:
            worked[entry.day] += entry.hours
    ordinary = overtime = holiday = NO_HOURS
    for day, hours in worked.items():
        if day in HOLIDAYS:
            holiday += hours
        else:
            ordinary += min(hours, settings.daily_threshold)
            overtime += max(hours - settings.daily_threshold, NO_HOURS)
    shifts = sum(1 for hours in worked.values() if hours > 0)
    return Hours(ordinary, overtime, holiday, sick, shifts)
