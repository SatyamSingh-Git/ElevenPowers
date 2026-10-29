"""`payroll doctor`: reads everything in a data directory and reports what it cannot use."""
from payroll.config import load_settings
from payroll.errors import PayrollError
from payroll.storage.employee_store import load_employees
from payroll.storage.payrun_file import read_payrun
from payroll.storage.timesheet_store import read_timesheet


def diagnose(data):
    """(problems, notes): problems stop payroll from working; notes are worth knowing."""
    problems, notes = [], []
    try:
        settings = load_settings(data.root)
    except PayrollError as error:
        return [f"payroll.ini: {error}"], notes
    try:
        employees = load_employees(data)
    except PayrollError as error:
        problems.append(str(error))
        employees = {}
    if not employees:
        notes.append("there are no employees yet")

    calendar = settings.calendar()
    for path in sorted((data.root / "timesheets").glob("*.csv")):
        try:
            calendar.period(path.stem)
            entries = read_timesheet(data, path.stem)
        except (PayrollError, KeyError, ValueError) as error:
            problems.append(f"timesheets/{path.name}: {error}")
            continue
        strangers = sorted({entry.employee_id for entry in entries} - set(employees))
        if strangers:
            problems.append(f"timesheets/{path.name}: names unknown employee {strangers[0]}")

    for path in sorted(data.runs.glob("*.json")):
        try:
            run = read_payrun(path)
        except (PayrollError, KeyError, ValueError) as error:
            problems.append(f"runs/{path.name}: {error}")
            continue
        if run.payslips and not data.bank_file(run.period.id).exists():
            notes.append(f"{run.period.id} was paid but has no bank file yet")
    return problems, notes
