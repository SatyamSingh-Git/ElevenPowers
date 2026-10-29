"""`payroll timesheet days`: how many people worked, and for how long, on each day of a period."""
from collections import defaultdict
from decimal import Decimal

from payroll._generated import HOLIDAYS
from payroll.model.timesheet import format_hours
from payroll.reports.formatting import table


def day_rows(period, entries):
    """(date, weekday, people working, work hours, sick hours, note) for every day of the period."""
    people = defaultdict(set)
    work = defaultdict(Decimal)
    sick = defaultdict(Decimal)
    for entry in entries:
        if entry.kind == "sick":
            sick[entry.day] += entry.hours
        else:
            people[entry.day].add(entry.employee_id)
            work[entry.day] += entry.hours
    return [
        (day, day.strftime("%a"), len(people[day]), work[day], sick[day], HOLIDAYS.get(day, ""))
        for day in period.days()
    ]


def render_days(period, rows):
    body = [
        [day.isoformat(), weekday, count, format_hours(worked), format_hours(off_sick), note]
        for day, weekday, count, worked, off_sick, note in rows
    ]
    header = ("date", "day", "people", "work", "sick", "")
    return f"Days in {period.describe()}\n\n" + table(header, body, numeric=(2, 3, 4))
