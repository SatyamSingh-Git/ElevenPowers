"""A week's plan as an iCalendar file, one event per meal.

The week is given by the date of its Monday, so the same plan and date always
write the same file. Times are local ("floating"), as a kitchen calendar wants.
"""
from datetime import date, datetime, time, timedelta
from pathlib import Path

from ..core.plan import DAYS
from ..errors import PlanError

MEAL_TIMES = {
    "breakfast": time(8, 0),
    "lunch": time(12, 30),
    "snack": time(16, 0),
    "dinner": time(19, 0),
}
MEAL_LENGTH = timedelta(minutes=45)
PRODUCT = "-//recipebox//meal plan//EN"


def parse_week(text):
    """The Monday a `--week-of` value names; any other day is refused."""
    try:
        monday = date.fromisoformat(text)
    except ValueError as error:
        raise PlanError(f"cannot read date {text}, expected YYYY-MM-DD") from error
    if monday.weekday() != 0:
        raise PlanError(f"--week-of must be a Monday, {text} is a {DAYS[monday.weekday()]}")
    return monday


def _stamp(moment):
    return moment.strftime("%Y%m%dT%H%M%S")


def _escape(text):
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")


def plan_events(plan, monday):
    """(start, end, title, uid) for every planned meal, in day and meal order."""
    events = []
    for day in plan.days():
        when = monday + timedelta(days=DAYS.index(day))
        for entry in plan.on(day):
            start = datetime.combine(when, MEAL_TIMES[entry.meal])
            uid = f"{when.isoformat()}-{entry.meal}-{entry.recipe.id}@recipebox"
            events.append((start, start + MEAL_LENGTH, f"{entry.meal.capitalize()}: {entry.recipe.title}", uid))
    return events


def plan_to_ics(plan, monday):
    created = _stamp(datetime.combine(monday, time(0, 0)))
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:{PRODUCT}"]
    for start, end, title, uid in plan_events(plan, monday):
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{created}",
            f"DTSTART:{_stamp(start)}",
            f"DTEND:{_stamp(end)}",
            f"SUMMARY:{_escape(title)}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    # iCalendar lines end in CRLF.
    return "\r\n".join(lines) + "\r\n"


def save_calendar(plan, monday, path):
    Path(path).write_bytes(plan_to_ics(plan, monday).encode("utf-8"))
    return len(plan_events(plan, monday))
