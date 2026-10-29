"""A pay run: a payslip for every active employee for one period, saved to runs/<period>.json."""
from itertools import groupby
from operator import attrgetter

from payroll.errors import PayrollError
from payroll.model.money import round_money, total
from payroll.model.payslip import Line, PayRun, Payslip
from payroll.rules.allowances import allowance_lines
from payroll.rules.deductions import deduction_lines
from payroll.rules.overtime import split_hours
from payroll.rules.tax import period_tax
from payroll.storage.employee_store import load_employees
from payroll.storage.payrun_file import read_payrun, write_payrun
from payroll.storage.timesheet_store import read_timesheet


def run_payroll(data, settings, period_id, replace=False):
    calendar = settings.calendar()
    period = calendar.period(period_id)
    path = data.run(period.id)
    if path.exists() and not replace:
        raise PayrollError(f"pay run {period.id} already exists; use --replace")
    employees = load_employees(data)
    entries = read_timesheet(data, period.id)
    by_employee = {employee_id: list(rows) for employee_id, rows in groupby(entries, attrgetter("employee_id"))}
    unknown = sorted(set(by_employee) - set(employees))
    if unknown:
        raise PayrollError(f"timesheet for {period.id} names unknown employee {unknown[0]}")
    payslips = []
    for employee in employees.values():
        rows = by_employee.get(employee.id, [])
        # Hourly staff with no hours this period are not paid and get no payslip.
        if not employee.active or (employee.hourly and not rows):
            continue
        hours = split_hours(rows, settings)
        payslips.append(build_payslip(employee, hours, settings, calendar.periods_per_year))
    run = PayRun(period, tuple(payslips))
    write_payrun(path, run)
    return run


def build_payslip(employee, hours, settings, periods_per_year):
    lines = _wage_lines(employee, hours, settings, periods_per_year)
    lines += allowance_lines(employee.allowances, hours)
    gross = total(line.amount for line in lines)
    tax = period_tax(gross, periods_per_year)
    deductions = deduction_lines(employee.deductions, gross)
    deducted = total(line.amount for line in deductions)
    return Payslip(
        employee_id=employee.id,
        name=employee.name,
        lines=tuple(lines + deductions),
        gross=gross,
        tax=tax,
        deductions=deducted,
        net=gross - tax - deducted,
    )


def _wage_lines(employee, hours, settings, periods_per_year):
    if not employee.hourly:
        return [Line("basic", "Salary", round_money(employee.rate / periods_per_year))]
    lines = []
    for kind, label, worked, multiplier in (
        ("basic", "Ordinary hours", hours.ordinary, 1),
        ("overtime", "Overtime", hours.overtime, settings.overtime_multiplier),
        ("holiday", "Public holiday", hours.holiday, settings.holiday_multiplier),
        ("sick", "Sick leave", hours.sick, 1),
    ):
        if worked:
            rate = round_money(employee.rate * multiplier)
            lines.append(Line(kind, label, round_money(worked * rate), hours=worked, rate=rate))
    return lines


def list_runs(data):
    return [read_payrun(path) for path in sorted(data.runs.glob("*.json"))]


def load_run(data, period_id):
    return read_payrun(data.run(period_id))


def void_run(data, period_id):
    """Deletes a pay run and its bank file so the period can be paid afresh; returns what was removed."""
    run = load_run(data, period_id)
    removed = []
    for path in (data.run(run.period.id), data.bank_file(run.period.id)):
        if path.exists():
            path.unlink()
            removed.append(path)
    return removed
