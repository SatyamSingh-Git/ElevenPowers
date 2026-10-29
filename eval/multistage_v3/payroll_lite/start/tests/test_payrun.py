from decimal import Decimal

import pytest

from helpers import entry, hourly, salaried, write_employees
from payroll.errors import PayrollError
from payroll.services.payrun import load_run, run_payroll
from payroll.storage.timesheet_store import write_timesheet


def test_hourly_pay_with_overtime_and_a_deduction(data, settings):
    write_employees(data, hourly("E001", "25.00", deductions=[{"kind": "percent", "label": "Pension", "rate": "5"}]))
    write_timesheet(data, "2026-W01", [entry("E001", "2026-01-05", "9"), entry("E001", "2026-01-06", "8")])
    slip = run_payroll(data, settings, "2026-W01").payslip_for("E001")
    assert [(line.kind, line.hours, line.rate, line.amount) for line in slip.lines] == [
        ("basic", Decimal("16"), Decimal("25.00"), Decimal("400.00")),
        ("overtime", Decimal("1"), Decimal("37.50"), Decimal("37.50")),
        ("deduction", None, None, Decimal("21.88")),
    ]
    assert (slip.gross, slip.tax, slip.deductions, slip.net) == (
        Decimal("437.50"), Decimal("31.01"), Decimal("21.88"), Decimal("384.61"))


def test_salaried_pay_ignores_hours(data, settings):
    write_employees(data, salaried("S001", "52000.00"))
    write_timesheet(data, "2026-W01", [entry("S001", "2026-01-05", "12")])
    slip = run_payroll(data, settings, "2026-W01").payslip_for("S001")
    assert slip.gross == Decimal("1000.00")
    assert slip.tax == Decimal("135.58")


def test_hourly_staff_without_hours_get_no_payslip(data, settings):
    write_employees(data, hourly("E001"), salaried("S001"))
    run = run_payroll(data, settings, "2026-W01")
    assert [slip.employee_id for slip in run.payslips] == ["S001"]


def test_people_who_have_left_are_not_paid(data, settings):
    write_employees(data, salaried("S001", active=False))
    assert run_payroll(data, settings, "2026-W01").payslips == ()


def test_saved_run_reads_back_the_same(data, settings):
    write_employees(data, hourly("E001", allowances=[{"kind": "fixed", "label": "Tools", "amount": "15.00"}]))
    write_timesheet(data, "2026-W01", [entry("E001", "2026-01-07", "7.25")])
    run = run_payroll(data, settings, "2026-W01")
    assert load_run(data, "2026-W01") == run


def test_a_period_is_paid_once_unless_replaced(data, settings):
    write_employees(data, salaried("S001"))
    run_payroll(data, settings, "2026-W01")
    with pytest.raises(PayrollError, match="pay run 2026-W01 already exists; use --replace"):
        run_payroll(data, settings, "2026-W01")
    run_payroll(data, settings, "2026-W01", replace=True)


def test_missing_run(data):
    with pytest.raises(PayrollError, match="no pay run for 2026-W09"):
        load_run(data, "2026-W09")
