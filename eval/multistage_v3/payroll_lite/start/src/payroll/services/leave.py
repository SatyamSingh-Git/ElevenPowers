"""Annual leave: balances in hours, built up from each pay run and used when leave is taken."""
from decimal import Decimal, ROUND_HALF_UP
import json

from payroll.errors import PayrollError
from payroll.model.timesheet import HUNDREDTH, format_hours, parse_hours
from payroll.services.payrun import load_run
from payroll.storage.employee_store import load_employees
from payroll.storage.files import write_text_atomic

# Four weeks a year: hourly staff earn 4/52 of an hour for every ordinary hour paid.
HOURLY_SHARE = Decimal(4) / Decimal(52)
SALARIED_HOURS_PER_YEAR = Decimal(160)
LEAVE_FILE = "leave.json"


def _load(data):
    path = data.root / LEAVE_FILE
    if not path.exists():
        return {}, []
    document = json.loads(path.read_text(encoding="utf-8"))
    balances = {employee_id: Decimal(hours) for employee_id, hours in document["balances"].items()}
    return balances, document["accrued"]


def _save(data, balances, accrued):
    document = {
        "balances": {employee_id: format_hours(balances[employee_id]) for employee_id in sorted(balances)},
        "accrued": sorted(accrued),
    }
    write_text_atomic(data.root / LEAVE_FILE, json.dumps(document, indent=2) + "\n")


def accrue(data, settings, period_id):
    """Adds the leave earned in a paid period; each period counts once."""
    run = load_run(data, period_id)
    balances, accrued = _load(data)
    if run.period.id in accrued:
        raise PayrollError(f"leave for {run.period.id} has already been added")
    employees = load_employees(data)
    periods_per_year = settings.calendar().periods_per_year
    earned = {}
    for slip in run.payslips:
        employee = employees.get(slip.employee_id)
        if employee is None:
            continue
        if employee.hourly:
            hours = sum((line.hours for line in slip.lines if line.kind == "basic"), Decimal(0)) * HOURLY_SHARE
        else:
            hours = SALARIED_HOURS_PER_YEAR / periods_per_year
        earned[slip.employee_id] = hours.quantize(HUNDREDTH, rounding=ROUND_HALF_UP)
        balances[slip.employee_id] = balances.get(slip.employee_id, Decimal(0)) + earned[slip.employee_id]
    _save(data, balances, accrued + [run.period.id])
    return earned


def take(data, employee_id, hours_text):
    hours = parse_hours(hours_text)
    if hours is None or hours <= 0:
        raise PayrollError(f"leave hours must be more than 0: {hours_text}")
    balances, accrued = _load(data)
    balance = balances.get(employee_id, Decimal(0))
    if hours > balance:
        raise PayrollError(f"{employee_id} has only {format_hours(balance)} hours of leave")
    balances[employee_id] = balance - hours
    _save(data, balances, accrued)
    return balances[employee_id]


def leave_balances(data):
    return _load(data)[0]
