"""Two paid weeks: the amounts paid to an hourly and a salaried employee, period by period and for the year."""
import csv
import io
import json
from decimal import Decimal

import pytest

from payroll.cli import main

SETTINGS = "[company]\nname = Harbour Bakery\npay_frequency = weekly\nfirst_period_start = 2026-01-05\n"
EMPLOYEES = [
    {"id": "E001", "name": "Ana Lima", "pay_type": "hourly", "rate": "25.00",
     "bank_account": "11-1111-0000001-00",
     "deductions": [{"kind": "percent", "label": "Pension", "rate": "5"}]},
    {"id": "E002", "name": "Ben Okafor", "pay_type": "hourly", "rate": "30.00",
     "bank_account": "22-2222-0000002-00",
     "allowances": [{"kind": "per_shift", "label": "Meal", "amount": "8.00"}],
     "deductions": [{"kind": "fixed", "label": "Union", "amount": "12.00"}]},
    {"id": "E003", "name": "Cara Diaz", "pay_type": "salaried", "rate": "52000.00",
     "bank_account": "33-3333-0000003-00",
     "allowances": [{"kind": "fixed", "label": "Phone", "amount": "10.00"}]},
]
WEEKS = {
    "2026-W01": [
        "E002,2026-01-05,8,work", "E001,2026-01-05,8,work", "E002,2026-01-06,8,", "E001,2026-01-06,9,work",
        "E001,2026-01-07,8,work", "E002,2026-01-07,10,work", "E001,2026-01-08,7.5,work", "E002,2026-01-08,4,sick",
        "E001,2026-01-09,7.5,work", "E002,2026-01-09,8,work",
    ],
    "2026-W02": [
        "E001,2026-01-12,8,work", "E002,2026-01-12,8,work", "E002,2026-01-13,8,work", "E001,2026-01-13,8,work",
        "E001,2026-01-14,8,work", "E002,2026-01-14,8,work", "E002,2026-01-15,8,work", "E001,2026-01-16,6,work",
        "E002,2026-01-17,8,work", "E002,2026-01-18,8,work",
    ],
}


def cli(folder, capsys, *args):
    capsys.readouterr()
    code = main(["--data", str(folder), *args])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


@pytest.fixture
def books(tmp_path, capsys):
    (tmp_path / "payroll.ini").write_text(SETTINGS, encoding="utf-8")
    (tmp_path / "employees.json").write_text(json.dumps({"employees": EMPLOYEES}), encoding="utf-8")
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    for period, rows in WEEKS.items():
        sheet = uploads / f"{period}.csv"
        sheet.write_text("employee_id,date,hours,kind\n" + "\n".join(rows) + "\n", encoding="utf-8")
        code, _, err = cli(tmp_path, capsys, "timesheet", "import", str(sheet), "--period", period)
        assert code == 0, err
        code, _, err = cli(tmp_path, capsys, "run", "--period", period)
        assert code == 0, err
    return tmp_path


def payslip_amounts(folder, capsys, period, employee):
    code, out, err = cli(folder, capsys, "payslip", "--period", period, "--employee", employee)
    assert code == 0, err
    found = {}
    for line in out.splitlines():
        for label in ("Gross pay", "Tax", "Net pay"):
            if line.startswith(label):
                found[label] = Decimal(line.split()[-1].replace(",", ""))
    return found


def test_hourly_pay_with_overtime_and_a_public_holiday(books, capsys):
    # 39 ordinary hours and 1 hour of overtime; then 24 ordinary hours and 6 on Founders' Day.
    assert payslip_amounts(books, capsys, "2026-W01", "E001") == {
        "Gross pay": Decimal("1012.50"), "Tax": Decimal("139.33"), "Net pay": Decimal("822.54")}
    assert payslip_amounts(books, capsys, "2026-W02", "E001") == {
        "Gross pay": Decimal("900.00"), "Tax": Decimal("105.58"), "Net pay": Decimal("749.42")}


def test_salaried_pay_with_a_fixed_allowance(books, capsys):
    assert payslip_amounts(books, capsys, "2026-W01", "E003") == {
        "Gross pay": Decimal("1010.00"), "Tax": Decimal("138.58"), "Net pay": Decimal("871.42")}


def test_year_end_totals(books, capsys):
    code, out, err = cli(books, capsys, "year-end", "--year", "2026", "--format", "csv")
    assert code == 0, err
    year = {row["employee_id"]: row for row in csv.DictReader(io.StringIO(out))}
    amounts = ("gross", "tax", "deductions", "net")
    assert {name: Decimal(year["E001"][name]) for name in amounts} == {
        "gross": Decimal("1912.50"), "tax": Decimal("244.91"), "deductions": Decimal("95.63"),
        "net": Decimal("1571.96")}
    assert {name: Decimal(year["E003"][name]) for name in amounts} == {
        "gross": Decimal("2020.00"), "tax": Decimal("277.16"), "deductions": Decimal("0"),
        "net": Decimal("1742.84")}
    assert year["E001"]["name"] == "Ana Lima"


def test_a_paid_period_is_not_paid_twice(books, capsys):
    code, _, err = cli(books, capsys, "run", "--period", "2026-W01")
    assert code == 1
    assert err == "error: pay run 2026-W01 already exists; use --replace\n"
