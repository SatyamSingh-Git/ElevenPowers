from datetime import date
from decimal import Decimal

from helpers import entry
from payroll.model.payslip import Line, PayRun, Payslip
from payroll.model.period import PayPeriod
from payroll.reports.bank_file import bank_rows
from payroll.reports.hours import hours_rows, render_hours
from payroll.reports.journal import journal_lines, render_journal_csv
from payroll.reports.payslip import render_payslip
from payroll.reports.summary import render_csv, render_text
from payroll.services.yearend import YearTotals
from payroll.model.employee import Employee

PERIOD = PayPeriod("2026-W01", date(2026, 1, 5), date(2026, 1, 11), date(2026, 1, 14))


def slip(employee_id="E001", net="822.54"):
    lines = (
        Line("basic", "Ordinary hours", Decimal("975.00"), Decimal("39.00"), Decimal("25.00")),
        Line("overtime", "Overtime", Decimal("37.50"), Decimal("1.00"), Decimal("37.50")),
        Line("deduction", "Pension", Decimal("50.63")),
    )
    return Payslip(employee_id, "Ana Lima", lines, Decimal("1012.50"), Decimal("139.33"), Decimal("50.63"),
                   Decimal(net))


def test_payslip_lists_earnings_then_deductions():
    text = render_payslip("Test Bakery", PERIOD, slip())
    lines = text.splitlines()
    assert lines[:3] == ["Test Bakery", "Payslip for Ana Lima (E001)",
                         "Period 2026-W01: 2026-01-05 to 2026-01-11, paid 2026-01-14"]
    assert [line.split()[0] for line in lines[4:]] == [
        "Earnings", "Ordinary", "Overtime", "Gross", "Tax", "Deductions", "Pension", "Net"]
    assert lines[-1].endswith("822.54")
    assert "39.00 h x 25.00" in text


def test_hours_report_splits_overtime_and_holidays(settings):
    rows = hours_rows([
        entry("E002", "2026-01-12", "10"),
        entry("E002", "2026-01-16", "6"),
        entry("E001", "2026-01-13", "4", "sick"),
    ], settings)
    assert rows == [
        ("E001", 0, 0, 0, Decimal("4"), Decimal("4")),
        ("E002", Decimal("8"), Decimal("2"), Decimal("6"), 0, Decimal("16")),
    ]


def test_hours_report_text(settings):
    text = render_hours(PERIOD, hours_rows([entry("E001", "2026-01-05", "9.5")], settings))
    assert text.splitlines()[3].split() == ["E001", "8.0", "1.5", "0.0", "0.0", "9.5"]


def test_year_end_summary_formats():
    rows = [YearTotals("E001", "Ana Lima", Decimal("1912.50"), Decimal("244.91"), Decimal("95.63"),
                       Decimal("1571.96"))]
    assert render_csv(2026, rows) == (
        "employee_id,name,gross,tax,deductions,net\nE001,Ana Lima,1912.50,244.91,95.63,1571.96\n")
    assert "1,912.50" in render_text(2026, rows)
    assert render_text(2026, []) == "No pay runs were paid in 2026.\n"


def test_bank_rows_skip_nothing_to_pay():
    run = PayRun(PERIOD, (slip("E001"), slip("E002", "0.00")))
    employees = {"E001": Employee("E001", "Ana Lima", "hourly", Decimal("25"), "11-1111-0000001-00")}
    assert bank_rows(run, employees) == [["11-1111-0000001-00", "Ana Lima", "822.54", "PAY 2026-W01"]]


def test_journal_balances():
    run = PayRun(PERIOD, (slip("E001"), slip("E002")))
    lines = journal_lines(run)
    assert sum(line[1] for line in lines) == sum(line[2] for line in lines) == Decimal("2025.00")
    assert render_journal_csv(run, lines).splitlines()[0] == "account,debit,credit"
