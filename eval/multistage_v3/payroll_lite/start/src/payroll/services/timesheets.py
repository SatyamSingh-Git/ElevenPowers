"""Getting hours in: importing a supervisor's CSV, adding single rows, and a blank sheet to fill in."""
import csv
from datetime import date
import io
from pathlib import Path

from payroll.errors import PayrollError
from payroll.storage.employee_store import load_employees
from payroll.storage.timesheet_csv import REQUIRED_COLUMNS, check_row, duplicate_problem, parse_timesheet
from payroll.storage.timesheet_store import read_timesheet, write_timesheet


def import_timesheet(data, settings, period_id, path):
    """Replaces the period's stored timesheet with the file's rows, all or nothing."""
    period = settings.calendar().period(period_id)
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise PayrollError(f"no such file: {path}") from None
    entries = parse_timesheet(text, period, _active(data), settings.max_hours_per_day)
    write_timesheet(data, period.id, entries)
    return entries


def add_entry(data, settings, period_id, employee_id, day_text, hours_text, kind_text=None):
    period = settings.calendar().period(period_id)
    entries = read_timesheet(data, period.id)
    entry, problem = check_row(employee_id, day_text, hours_text, kind_text, period, _active(data),
                               settings.max_hours_per_day)
    if problem:
        raise PayrollError(problem)
    if any((e.employee_id, e.day, e.kind) == (entry.employee_id, entry.day, entry.kind) for e in entries):
        raise PayrollError(duplicate_problem(entry))
    write_timesheet(data, period.id, entries + [entry])
    return entry


def remove_entries(data, settings, period_id, employee_id, day_text, kind_text=None):
    """Removes an employee's rows for a day, or only those of one kind; returns how many went."""
    period = settings.calendar().period(period_id)
    try:
        day = date.fromisoformat(day_text)
    except ValueError:
        raise PayrollError(f"bad date {day_text}") from None
    entries = read_timesheet(data, period.id)
    kept = [
        entry for entry in entries
        if not (entry.employee_id == employee_id and entry.day == day and kind_text in (None, entry.kind))
    ]
    if len(kept) == len(entries):
        raise PayrollError(f"no hours for {employee_id} on {day.isoformat()}")
    write_timesheet(data, period.id, kept)
    return len(entries) - len(kept)


def stored_entries(data, settings, period_id):
    period = settings.calendar().period(period_id)
    return period, read_timesheet(data, period.id)


def blank_sheet(data, settings, period_id):
    """A CSV with a row for every active hourly employee on every day of the period, hours left empty."""
    period = settings.calendar().period(period_id)
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow((*REQUIRED_COLUMNS, "kind"))
    for employee in _active(data).values():
        if employee.hourly:
            for day in period.days():
                writer.writerow((employee.id, day.isoformat(), "", ""))
    return out.getvalue()


def _active(data):
    return {key: employee for key, employee in load_employees(data).items() if employee.active}
