"""`payroll hours`: each employee's hours from the stored timesheet, for checking before a pay run."""
from collections import defaultdict
from decimal import Decimal

from payroll._generated import HOLIDAYS
from payroll.reports.formatting import table

COLUMNS = ("employee", "ordinary", "overtime", "holiday", "sick", "total")


def hours_rows(entries, settings):
    """(employee, ordinary, overtime, holiday, sick, total) for each employee with hours,
    split the way the pay run pays them."""
    worked = defaultdict(lambda: defaultdict(Decimal))
    sick = defaultdict(Decimal)
    for entry in entries:
        if entry.kind == "sick":
            sick[entry.employee_id] += entry.hours
        else:
            worked[entry.employee_id][entry.day] += entry.hours
    rows = []
    for employee_id in sorted(set(worked) | set(sick)):
        ordinary = overtime = holiday = Decimal(0)
        for day, hours in worked[employee_id].items():
            if day in HOLIDAYS:
                holiday += hours
            else:
                ordinary += min(hours, settings.daily_threshold)
                overtime += max(hours - settings.daily_threshold, Decimal(0))
        off_sick = sick[employee_id]
        rows.append((employee_id, ordinary, overtime, holiday, off_sick, ordinary + overtime + holiday + off_sick))
    return rows


def render_hours(period, rows):
    if not rows:
        return f"No hours recorded for {period.id}.\n"
    body = [[row[0]] + [_hours(value) for value in row[1:]] for row in rows]
    body.append(["total"] + [_hours(sum(row[index] for row in rows)) for index in range(1, len(COLUMNS))])
    return f"Hours for {period.describe()}\n\n" + table(COLUMNS, body, numeric=range(1, len(COLUMNS)))


def _hours(value):
    return f"{value:.1f}"
