"""The `payroll` command."""
import argparse
from dataclasses import fields
from datetime import date
from pathlib import Path
import sys

from payroll import __version__
from payroll._generated import CALENDAR_VERSION
from payroll.config import load_settings
from payroll.errors import ImportRejected, PayrollError
from payroll.model.money import format_money, parse_money
from payroll.model.timesheet import format_hours
from payroll.reports.bank_file import bank_rows, check_rows, paid_total, write_bank_file
from payroll.reports.compare import compare_rows, render_compare
from payroll.reports.costs import department_costs, render_costs
from payroll.reports.formatting import table
from payroll.reports.hours import hours_rows, render_hours
from payroll.reports.journal import JOURNAL_FORMATS, journal_lines
from payroll.reports.payslip import render_payslip
from payroll.reports.run_summary import render_run, render_runs
from payroll.reports.staffing import day_rows, render_days
from payroll.reports.statement import render_statement, statement_name
from payroll.reports.summary import FORMATS
from payroll.services import employees as staff
from payroll.services import leave
from payroll.services.archive import archive_year
from payroll.services.checks import period_warnings
from payroll.services.doctor import diagnose
from payroll.services.payrun import list_runs, load_run, run_payroll, void_run
from payroll.services.reconcile import all_matched, load_payments, load_statement, reconcile
from payroll.services.timesheets import add_entry, blank_sheet, import_timesheet, remove_entries, stored_entries
from payroll.services.year_to_date import year_to_date
from payroll.services.yearend import year_totals
from payroll.rules.tax import period_tax
from payroll.storage.employee_csv import employees_csv, parse_employees
from payroll.storage.employee_store import load_employees, save_employees
from payroll.storage.files import DataDir, write_text_atomic


def main(argv=None):
    args = build_parser().parse_args(argv)
    data = DataDir(args.data)
    try:
        return args.handler(args, data)
    except ImportRejected as rejected:
        for problem in rejected.problems:
            print(f"error: {problem}", file=sys.stderr)
        print(f"error: {rejected}; nothing was imported", file=sys.stderr)
        return 1
    except PayrollError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


def build_parser():
    parser = argparse.ArgumentParser(prog="payroll", description="Payroll for a small business.")
    parser.add_argument("--data", default=".", help="data directory (default: the current directory)")
    parser.add_argument("--version", action="version", version=f"payroll {__version__} (calendar {CALENDAR_VERSION})")
    commands = parser.add_subparsers(dest="command", required=True)

    employees = commands.add_parser("employees", help="who is on the payroll").add_subparsers(
        dest="action", required=True)
    listing = employees.add_parser("list")
    listing.add_argument("--department")
    listing.add_argument("--all", action="store_true", help="include people who have left")
    listing.set_defaults(handler=employees_list)
    show = employees.add_parser("show")
    show.add_argument("employee")
    show.set_defaults(handler=employees_show)
    add = employees.add_parser("add")
    add.add_argument("--id", required=True)
    add.add_argument("--name", required=True)
    add.add_argument("--pay-type", required=True, choices=("hourly", "salaried"))
    add.add_argument("--rate", required=True, help="hourly rate, or yearly salary")
    add.add_argument("--bank-account", required=True)
    add.add_argument("--department", default="General")
    add.set_defaults(handler=employees_add)
    bulk = employees.add_parser("import", help="add employees from a CSV file")
    bulk.add_argument("file")
    bulk.set_defaults(handler=employees_import)
    export = employees.add_parser("export", help="write employees as CSV, in the layout import reads")
    export.add_argument("--out")
    export.set_defaults(handler=employees_export)
    update = employees.add_parser("update")
    update.add_argument("employee")
    update.add_argument("--name")
    update.add_argument("--bank-account")
    update.add_argument("--department")
    update.set_defaults(handler=employees_update)
    for name, active in (("leave", False), ("rejoin", True)):
        command = employees.add_parser(name)
        command.add_argument("employee")
        command.set_defaults(handler=employees_set_active, active=active)
    rate = employees.add_parser("rate")
    rate.add_argument("employee")
    rate.add_argument("rate")
    rate.set_defaults(handler=employees_rate)
    allowance = employees.add_parser("allowance")
    allowance.add_argument("employee")
    allowance.add_argument("--kind", required=True)
    allowance.add_argument("--amount", required=True)
    allowance.add_argument("--label")
    allowance.set_defaults(handler=employees_allowance)
    deduction = employees.add_parser("deduction")
    deduction.add_argument("employee")
    deduction.add_argument("--kind", required=True)
    deduction.add_argument("--label")
    deduction.add_argument("--amount")
    deduction.add_argument("--rate")
    deduction.set_defaults(handler=employees_deduction)
    drop = employees.add_parser("drop", help="remove an allowance or deduction by its label")
    drop.add_argument("employee")
    drop.add_argument("label")
    drop.set_defaults(handler=employees_drop)

    periods = commands.add_parser("periods", help="list the pay periods of a year, or find a day's period")
    which = periods.add_mutually_exclusive_group(required=True)
    which.add_argument("--year", type=int)
    which.add_argument("--date", type=date.fromisoformat, help="YYYY-MM-DD")
    periods.set_defaults(handler=periods_list)
    commands.add_parser("settings", help="the settings in force, defaults included").set_defaults(
        handler=settings_show)
    commands.add_parser("doctor", help="check that everything in the data directory can be read").set_defaults(
        handler=doctor_show)
    tax = commands.add_parser("tax", help="the tax on a period's gross pay")
    tax.add_argument("--gross", required=True)
    tax.set_defaults(handler=tax_show)

    timesheet = commands.add_parser("timesheet", help="hours for a period").add_subparsers(
        dest="action", required=True)
    upload = timesheet.add_parser("import")
    upload.add_argument("file")
    upload.add_argument("--period", required=True)
    upload.set_defaults(handler=timesheet_import)
    one = timesheet.add_parser("add")
    one.add_argument("--period", required=True)
    one.add_argument("--employee", required=True)
    one.add_argument("--date", required=True)
    one.add_argument("--hours", required=True)
    one.add_argument("--kind")
    one.set_defaults(handler=timesheet_add)
    listing = timesheet.add_parser("show")
    listing.add_argument("--period", required=True)
    listing.add_argument("--employee", help="only this employee's rows")
    listing.set_defaults(handler=timesheet_show)
    blank = timesheet.add_parser("blank", help="a sheet for supervisors to fill in")
    blank.add_argument("--period", required=True)
    blank.add_argument("--out")
    blank.set_defaults(handler=timesheet_blank)
    days = timesheet.add_parser("days", help="people and hours on each day of the period")
    days.add_argument("--period", required=True)
    days.set_defaults(handler=timesheet_days)
    remove = timesheet.add_parser("remove", help="remove an employee's hours for a day")
    remove.add_argument("--period", required=True)
    remove.add_argument("--employee", required=True)
    remove.add_argument("--date", required=True)
    remove.add_argument("--kind", help="only rows of this kind")
    remove.set_defaults(handler=timesheet_remove)

    run = commands.add_parser("run", help="pay everyone for a period")
    run.add_argument("--period", required=True)
    run.add_argument("--replace", action="store_true", help="run again over an existing pay run")
    run.set_defaults(handler=run_period)
    runs = commands.add_parser("runs", help="list pay runs")
    runs.add_argument("--year", type=int, help="only runs paid in this year")
    runs.set_defaults(handler=runs_list)
    void = commands.add_parser("void", help="delete a pay run and its bank file")
    void.add_argument("--period", required=True)
    void.set_defaults(handler=void_period)
    check = commands.add_parser("check", help="warnings to look at before paying a period")
    check.add_argument("--period", required=True)
    check.set_defaults(handler=check_period)
    compare = commands.add_parser("compare", help="net pay in one pay run against another")
    compare.add_argument("--period", required=True)
    compare.add_argument("--against", help="the earlier period (default: the one before)")
    compare.set_defaults(handler=compare_runs)
    costs = commands.add_parser("costs", help="gross pay by department for a pay run")
    costs.add_argument("--period", required=True)
    costs.set_defaults(handler=costs_show)
    journal = commands.add_parser("journal", help="the ledger entry for a pay run")
    journal.add_argument("--period", required=True)
    journal.add_argument("--format", choices=sorted(JOURNAL_FORMATS), default="text")
    journal.set_defaults(handler=journal_show)

    payslip = commands.add_parser("payslip")
    payslip.add_argument("--period", required=True)
    payslip.add_argument("--employee", required=True)
    payslip.set_defaults(handler=payslip_show)
    payslips = commands.add_parser("payslips", help="write every payslip of a pay run to a folder")
    payslips.add_argument("--period", required=True)
    payslips.add_argument("--out", required=True)
    payslips.set_defaults(handler=payslips_write)

    hours = commands.add_parser("hours", help="hours per employee from the stored timesheet")
    hours.add_argument("--period", required=True)
    hours.set_defaults(handler=hours_show)

    year_end = commands.add_parser("year-end", help="totals per employee for a year")
    year_end.add_argument("--year", type=int, required=True)
    year_end.add_argument("--format", choices=sorted(FORMATS), default="text")
    year_end.set_defaults(handler=year_end_show)
    statements = commands.add_parser("statements", help="write each employee's earnings statement for a year")
    statements.add_argument("--year", type=int, required=True)
    statements.add_argument("--out", required=True)
    statements.set_defaults(handler=statements_write)
    archive = commands.add_parser("archive", help="zip a year's pay runs, timesheets and bank files")
    archive.add_argument("--year", type=int, required=True)
    archive.add_argument("--out", required=True)
    archive.set_defaults(handler=archive_write)

    leave_commands = commands.add_parser("leave", help="annual leave balances").add_subparsers(
        dest="action", required=True)
    leave_commands.add_parser("show").set_defaults(handler=leave_show)
    accrue = leave_commands.add_parser("accrue", help="add the leave earned in a paid period")
    accrue.add_argument("--period", required=True)
    accrue.set_defaults(handler=leave_accrue)
    take = leave_commands.add_parser("take")
    take.add_argument("--employee", required=True)
    take.add_argument("--hours", required=True)
    take.set_defaults(handler=leave_take)

    bank = commands.add_parser("bank-file", help="write the bank's payment file for a pay run")
    bank.add_argument("--period", required=True)
    bank.add_argument("--out", help="default: bank/<period>.csv in the data directory")
    bank.set_defaults(handler=bank_file)

    matching = commands.add_parser("reconcile", help="check a bank statement against a payment file")
    matching.add_argument("--period", required=True)
    matching.add_argument("--statement", required=True)
    matching.add_argument("--bank-file", help="default: bank/<period>.csv in the data directory")
    matching.set_defaults(handler=reconcile_statement)
    return parser


def employees_list(args, data):
    employees = [
        e for e in load_employees(data).values()
        if (args.all or e.active) and args.department in (None, e.department)
    ]
    if not employees:
        print("No employees to list.")
        return 0
    rows = [[e.id, e.name, e.pay_type, "yes" if e.active else "no"] for e in employees]
    print(table(("id", "name", "pay_type", "active"), rows), end="")
    return 0


def employees_show(args, data):
    employee = staff.find_employee(load_employees(data), args.employee)
    print(f"{employee.id}  {employee.name}{'' if employee.active else '  (left)'}")
    print(f"  {employee.pay_type} in {employee.department}, paid {employee.describe_rate()} into {employee.bank_account}")
    for allowance in employee.allowances:
        print(f"  allowance {allowance.label}: {allowance.kind} {format_money(allowance.amount)}")
    for deduction in employee.deductions:
        params = ", ".join(f"{name} {value}" for name, value in deduction.params.items())
        print(f"  deduction {deduction.label}: {deduction.kind} {params}")
    return 0


def employees_add(args, data):
    employee = staff.add_employee(data, args.id, args.name, args.pay_type, args.rate, args.bank_account,
                                  args.department)
    print(f"Added {employee.id} {employee.name}.")
    return 0


def employees_import(args, data):
    try:
        text = Path(args.file).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise PayrollError(f"no such file: {args.file}") from None
    employees = load_employees(data)
    added = parse_employees(text, employees)
    save_employees(data, {**employees, **added})
    print(f"Added {len(added)} employees.")
    return 0


def employees_export(args, data):
    text = employees_csv(load_employees(data))
    if args.out:
        write_text_atomic(Path(args.out), text)
        print(f"Wrote {args.out}.")
    else:
        print(text, end="")
    return 0


def employees_update(args, data):
    employee = staff.update_details(data, args.employee, args.name, args.bank_account, args.department)
    print(f"Updated {employee.id} {employee.name}.")
    return 0


def employees_set_active(args, data):
    employee = staff.set_active(data, args.employee, args.active)
    print(f"{employee.id} is {'active' if employee.active else 'no longer paid'}.")
    return 0


def employees_rate(args, data):
    employee = staff.set_rate(data, args.employee, args.rate)
    print(f"{employee.id} now earns {employee.describe_rate()}.")
    return 0


def employees_allowance(args, data):
    allowance = staff.add_allowance(data, args.employee, args.kind, args.label, args.amount)
    print(f"Added allowance {allowance.label} to {args.employee}.")
    return 0


def employees_deduction(args, data):
    values = {"amount": args.amount, "rate": args.rate}
    deduction = staff.add_deduction(data, args.employee, args.kind, args.label, values)
    print(f"Added deduction {deduction.label} to {args.employee}.")
    return 0


def employees_drop(args, data):
    staff.remove_extra(data, args.employee, args.label)
    print(f"Removed {args.label} from {args.employee}.")
    return 0


def periods_list(args, data):
    calendar = load_settings(args.data).calendar()
    if args.date:
        periods = [calendar.period_containing(args.date)]
    else:
        periods = calendar.periods_in_year(args.year)
    rows = [[p.id, p.start.isoformat(), p.end.isoformat(), p.pay_date.isoformat()] for p in periods]
    print(table(("period", "start", "end", "paid"), rows), end="")
    return 0


def settings_show(args, data):
    settings = load_settings(args.data)
    for field in fields(settings):
        print(f"{field.name} = {getattr(settings, field.name)}")
    return 0


def tax_show(args, data):
    settings = load_settings(args.data)
    gross = parse_money(args.gross, "gross")
    tax = period_tax(gross, settings.calendar().periods_per_year)
    print(f"Tax on {format_money(gross)} paid {settings.pay_frequency}: {format_money(tax)}")
    return 0


def doctor_show(args, data):
    problems, notes = diagnose(data)
    for problem in problems:
        print(f"problem: {problem}")
    for note in notes:
        print(f"note: {note}")
    if not problems:
        print("Everything can be read.")
    return 1 if problems else 0


def timesheet_import(args, data):
    entries = import_timesheet(data, load_settings(args.data), args.period, args.file)
    print(f"Imported {len(entries)} rows for {args.period}.")
    return 0


def timesheet_add(args, data):
    entry = add_entry(data, load_settings(args.data), args.period, args.employee, args.date, args.hours, args.kind)
    print(f"Added {format_hours(entry.hours)} {entry.kind} hours for {entry.employee_id} on {entry.day.isoformat()}.")
    return 0


def timesheet_show(args, data):
    period, entries = stored_entries(data, load_settings(args.data), args.period)
    entries = [e for e in entries if args.employee in (None, e.employee_id)]
    if not entries:
        print(f"No hours recorded for {period.id}.")
        return 0
    rows = [[e.employee_id, e.day.isoformat(), format_hours(e.hours), e.kind] for e in entries]
    print(table(("employee", "date", "hours", "kind"), rows, numeric=(2,)), end="")
    return 0


def timesheet_blank(args, data):
    sheet = blank_sheet(data, load_settings(args.data), args.period)
    if args.out:
        write_text_atomic(Path(args.out), sheet)
        print(f"Wrote {args.out}.")
    else:
        print(sheet, end="")
    return 0


def timesheet_days(args, data):
    period, entries = stored_entries(data, load_settings(args.data), args.period)
    print(render_days(period, day_rows(period, entries)), end="")
    return 0


def timesheet_remove(args, data):
    count = remove_entries(data, load_settings(args.data), args.period, args.employee, args.date, args.kind)
    print(f"Removed {count} rows.")
    return 0


def run_period(args, data):
    run = run_payroll(data, load_settings(args.data), args.period, replace=args.replace)
    print(render_run(run), end="")
    return 0


def runs_list(args, data):
    runs = [run for run in list_runs(data) if args.year in (None, run.period.pay_date.year)]
    print(render_runs(runs), end="")
    return 0


def void_period(args, data):
    removed = void_run(data, args.period)
    print(f"Removed {', '.join(path.name for path in removed)}.")
    return 0


def journal_show(args, data):
    run = load_run(data, args.period)
    print(JOURNAL_FORMATS[args.format](run, journal_lines(run)), end="")
    return 0


def check_period(args, data):
    warnings = period_warnings(data, load_settings(args.data), args.period)
    for warning in warnings:
        print(f"warning: {warning}")
    if not warnings:
        print(f"Nothing to check for {args.period}.")
    return 0


def compare_runs(args, data):
    later = load_run(data, args.period)
    against = args.against
    if against is None:
        before = load_settings(args.data).calendar().previous(later.period)
        if before is None:
            raise PayrollError(f"{later.period.id} is the first period; give --against")
        against = before.id
    earlier = load_run(data, against)
    print(render_compare(earlier, later, compare_rows(earlier, later)), end="")
    return 0


def costs_show(args, data):
    run = load_run(data, args.period)
    print(render_costs(run, department_costs(run, load_employees(data))), end="")
    return 0


def payslip_show(args, data):
    run = load_run(data, args.period)
    slip = run.payslip_for(args.employee)
    if slip is None:
        raise PayrollError(f"no payslip for {args.employee} in {run.period.id}")
    company = load_settings(args.data).company_name
    print(render_payslip(company, run.period, slip, year_to_date(data, run, slip.employee_id)), end="")
    return 0


def payslips_write(args, data):
    run = load_run(data, args.period)
    company = load_settings(args.data).company_name
    folder = Path(args.out)
    for slip in run.payslips:
        text = render_payslip(company, run.period, slip, year_to_date(data, run, slip.employee_id))
        write_text_atomic(folder / f"{run.period.id}-{slip.employee_id}.txt", text)
    print(f"Wrote {len(run.payslips)} payslips to {folder}.")
    return 0


def hours_show(args, data):
    settings = load_settings(args.data)
    period, entries = stored_entries(data, settings, args.period)
    print(render_hours(period, hours_rows(entries, settings)), end="")
    return 0


def year_end_show(args, data):
    print(FORMATS[args.format](args.year, year_totals(data, args.year)), end="")
    return 0


def statements_write(args, data):
    rows = year_totals(data, args.year)
    if not rows:
        raise PayrollError(f"no pay runs were paid in {args.year}")
    company = load_settings(args.data).company_name
    folder = Path(args.out)
    for row in rows:
        write_text_atomic(folder / statement_name(args.year, row), render_statement(company, args.year, row))
    print(f"Wrote {len(rows)} statements to {folder}.")
    return 0


def archive_write(args, data):
    names = archive_year(data, args.year, args.out)
    print(f"Archived {len(names)} files to {args.out}.")
    return 0


def leave_show(args, data):
    balances = leave.leave_balances(data)
    if not balances:
        print("No leave recorded yet.")
        return 0
    employees = load_employees(data)
    rows = [
        [employee_id, employees[employee_id].name if employee_id in employees else "", format_hours(hours)]
        for employee_id, hours in sorted(balances.items())
    ]
    print(table(("employee", "name", "hours"), rows, numeric=(2,)), end="")
    return 0


def leave_accrue(args, data):
    earned = leave.accrue(data, load_settings(args.data), args.period)
    for employee_id, hours in earned.items():
        print(f"{employee_id} earned {format_hours(hours)} hours")
    return 0


def leave_take(args, data):
    left = leave.take(data, args.employee, args.hours)
    print(f"{args.employee} has {format_hours(left)} hours of leave left.")
    return 0


def bank_file(args, data):
    run = load_run(data, args.period)
    rows = bank_rows(run, load_employees(data))
    check_rows(rows)
    path = Path(args.out) if args.out else data.bank_file(run.period.id)
    write_bank_file(path, rows)
    print(f"Wrote {len(rows)} payments totalling {format_money(paid_total(run))} to {path}.")
    return 0


def reconcile_statement(args, data):
    path = Path(args.bank_file) if args.bank_file else data.bank_file(args.period)
    results = reconcile(load_payments(path), load_statement(args.statement))
    for account, name, status in results:
        print(f"{account} {name}: {status}")
    return 0 if all_matched(results) else 1
