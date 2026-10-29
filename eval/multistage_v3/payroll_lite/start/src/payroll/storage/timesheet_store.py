"""timesheets/<period>.csv: the hours accepted for a period, as the pay run reads them."""
import csv
from datetime import date
from decimal import Decimal
import io

from payroll.model.timesheet import TimesheetEntry, format_hours
from payroll.storage.files import write_text_atomic

COLUMNS = ("employee_id", "date", "hours", "kind")


def write_timesheet(data, period_id, entries):
    """Replaces the stored timesheet, rows sorted by employee, then date, then kind."""
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(COLUMNS)
    for entry in sorted(entries, key=_order):
        writer.writerow([entry.employee_id, entry.day.isoformat(), format_hours(entry.hours), entry.kind])
    write_text_atomic(data.timesheet(period_id), out.getvalue())


def _order(entry):
    return entry.employee_id, entry.day, entry.kind


def read_timesheet(data, period_id):
    """The stored rows in file order; an empty list when nothing has been imported."""
    path = data.timesheet(period_id)
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            TimesheetEntry(row["employee_id"], date.fromisoformat(row["date"]), Decimal(row["hours"]), row["kind"])
            for row in csv.DictReader(handle)
        ]
