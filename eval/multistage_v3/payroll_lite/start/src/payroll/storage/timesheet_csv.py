"""Reading a timesheet uploaded as CSV: one row per employee, day and kind of hours."""
import csv
from datetime import date
import io

from payroll.errors import ImportRejected, PayrollError
from payroll.model.timesheet import DEFAULT_KIND, KINDS, TimesheetEntry, parse_hours

REQUIRED_COLUMNS = ("employee_id", "date", "hours")


def parse_timesheet(text, period, employees, max_hours):
    """Every row as an entry, or ImportRejected listing each bad row by its line in the file."""
    reader = csv.DictReader(io.StringIO(text))
    columns = [name.strip() for name in reader.fieldnames or []]
    for column in REQUIRED_COLUMNS:
        if column not in columns:
            raise PayrollError(f"missing column {column}")
    reader.fieldnames = columns
    entries, problems, seen = [], [], set()
    for row in reader:
        # A blank sheet has a row for every day; the days nobody filled in are not rows to reject.
        if not (row.get("hours") or "").strip():
            continue
        entry, problem = check_row(row.get("employee_id"), row.get("date"), row.get("hours"), row.get("kind"),
                                   period, employees, max_hours)
        if entry is not None:
            if (entry.employee_id, entry.day, entry.kind) in seen:
                problem = duplicate_problem(entry)
            else:
                seen.add((entry.employee_id, entry.day, entry.kind))
                entries.append(entry)
                continue
        problems.append(f"line {reader.line_num}: {problem}")
    if problems:
        raise ImportRejected(problems)
    return entries


def check_row(employee_id, day_text, hours_text, kind_text, period, employees, max_hours):
    """(entry, None) for a good row, (None, problem) for the first thing wrong with it."""
    employee_id = (employee_id or "").strip()
    if employee_id not in employees:
        return None, f"unknown employee {employee_id}"
    try:
        day = date.fromisoformat((day_text or "").strip())
    except ValueError:
        return None, f"bad date {day_text}"
    if not period.contains(day):
        return None, f"{day.isoformat()} is outside period {period.id}"
    hours = parse_hours(hours_text or "")
    if hours is None or not 0 < hours <= max_hours:
        return None, f"hours must be more than 0 and at most {max_hours}"
    kind = (kind_text or "").strip() or DEFAULT_KIND
    if kind not in KINDS:
        return None, f"unknown kind {kind}"
    return TimesheetEntry(employee_id, day, hours, kind), None


def duplicate_problem(entry):
    return f"duplicate row for {entry.employee_id} on {entry.day.isoformat()}"
