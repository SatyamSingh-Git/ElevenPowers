"""`payroll check`: things worth a second look before a period is paid."""
from collections import defaultdict
from decimal import Decimal

from payroll._generated import HOLIDAYS
from payroll.model.timesheet import format_hours
from payroll.storage.employee_store import load_employees
from payroll.storage.timesheet_store import read_timesheet

# Longer than this in one day is allowed, but usually a typing mistake.
LONG_DAY = Decimal("12")


def period_warnings(data, settings, period_id):
    """Warnings for the period, in the order a payroll clerk would want to read them."""
    period = settings.calendar().period(period_id)
    employees = load_employees(data)
    entries = read_timesheet(data, period.id)
    warnings = []
    if data.run(period.id).exists():
        warnings.append(f"{period.id} has already been paid; paying it again needs --replace")
    if not entries:
        warnings.append(f"no hours have been recorded for {period.id}")

    named = {entry.employee_id for entry in entries}
    for employee_id in sorted(named - set(employees)):
        warnings.append(f"{employee_id} has hours but is not on the payroll")
    for employee_id in sorted(named & set(employees)):
        employee = employees[employee_id]
        if not employee.active:
            warnings.append(f"{employee_id} has hours but has left, so will not be paid")
        elif not employee.hourly:
            warnings.append(f"{employee_id} is salaried; their hours are kept but do not change their pay")
    for employee in employees.values():
        if employee.active and employee.hourly and employee.id not in named:
            warnings.append(f"{employee.id} {employee.name} has no hours and will not be paid")

    worked = defaultdict(Decimal)
    for entry in entries:
        worked[(entry.employee_id, entry.day)] += entry.hours
    for (employee_id, day), hours in sorted(worked.items()):
        if hours > LONG_DAY:
            warnings.append(f"{employee_id} has {format_hours(hours)} hours on {day.isoformat()}")
        if day in HOLIDAYS:
            warnings.append(f"{employee_id} worked on {HOLIDAYS[day]} ({day.isoformat()}), paid at the holiday rate")
        if hours > settings.max_hours_per_day:
            warnings.append(f"{employee_id} has more than {settings.max_hours_per_day} hours in total on {day.isoformat()}")
    return warnings
