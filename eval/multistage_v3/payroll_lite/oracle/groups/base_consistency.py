"""Two paid weeks for three employees: every output agrees with the pay runs behind it."""
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
ACCOUNTS = {employee["id"]: employee["bank_account"] for employee in EMPLOYEES}
# Supervisors list the week day by day, so each person's rows are spread through the file.
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
HOURLY = ("E001", "E002")


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


def payslip(folder, capsys, period, employee):
    code, out, err = cli(folder, capsys, "payslip", "--period", period, "--employee", employee)
    assert code == 0, err
    return out


def amount(text, label):
    for line in text.splitlines():
        if line.startswith(label):
            return Decimal(line.split()[-1].replace(",", ""))
    raise AssertionError(f"no {label} line in:\n{text}")


def run_hours(folder, period):
    """Per employee: (overtime hours, all hours) as the saved pay run paid them."""
    document = json.loads((folder / "runs" / f"{period}.json").read_text(encoding="utf-8"))
    paid = {}
    for slip in document["payslips"]:
        lines = [line for line in slip["lines"] if line["hours"] is not None]
        overtime = sum((Decimal(line["hours"]) for line in lines if line["kind"] == "overtime"), Decimal(0))
        paid[slip["employee_id"]] = (overtime, sum((Decimal(line["hours"]) for line in lines), Decimal(0)))
    return paid


def report_hours(folder, capsys, period):
    code, out, err = cli(folder, capsys, "hours", "--period", period)
    assert code == 0, err
    lines = out.splitlines()
    start = next(index for index, line in enumerate(lines) if line.split()[:1] == ["employee"])
    header = lines[start].split()
    rows = {}
    for line in lines[start + 1:]:
        cells = line.split()
        if cells and cells[0] in HOURLY:
            rows[cells[0]] = dict(zip(header[1:], (Decimal(cell) for cell in cells[1:])))
    return rows


def test_year_end_adds_up_the_payslips(books, capsys):
    code, out, err = cli(books, capsys, "year-end", "--year", "2026", "--format", "csv")
    assert code == 0, err
    year = {row["employee_id"]: row for row in csv.DictReader(io.StringIO(out))}
    assert sorted(year) == ["E001", "E002", "E003"]
    for employee in year:
        slips = [payslip(books, capsys, period, employee) for period in WEEKS]
        assert Decimal(year[employee]["gross"]) == sum(amount(slip, "Gross pay") for slip in slips)
        assert Decimal(year[employee]["net"]) == sum(amount(slip, "Net pay") for slip in slips)


def test_hours_report_matches_what_was_paid(books, capsys):
    for period in WEEKS:
        paid = run_hours(books, period)
        report = report_hours(books, capsys, period)
        assert sorted(report) == list(HOURLY)
        for employee in HOURLY:
            assert report[employee]["overtime"] == paid[employee][0], (period, employee)
            assert report[employee]["total"] == paid[employee][1], (period, employee)


def test_every_payslip_prints(books, capsys):
    for period in WEEKS:
        for employee in ACCOUNTS:
            assert "Net pay" in payslip(books, capsys, period, employee)


def test_journal_balances(books, capsys):
    for period in WEEKS:
        code, out, err = cli(books, capsys, "journal", "--period", period, "--format", "csv")
        assert code == 0, err
        rows = list(csv.DictReader(io.StringIO(out)))
        assert sum(Decimal(row["debit"]) for row in rows) == sum(Decimal(row["credit"]) for row in rows), out


def test_statement_with_every_payment_reconciles(books, capsys):
    code, _, err = cli(books, capsys, "bank-file", "--period", "2026-W01")
    assert code == 0, err
    statement = books / "statement.csv"
    lines = ["date,account,reference,amount", "2026-01-14,44-4444-0000004-00,RENT JAN,1500.00"]
    for employee, account in ACCOUNTS.items():
        net = amount(payslip(books, capsys, "2026-W01", employee), "Net pay")
        lines.append(f"2026-01-14,{account},PAY 2026-W01,{net}")
    statement.write_text("\n".join(lines) + "\n", encoding="utf-8")
    code, out, err = cli(books, capsys, "reconcile", "--period", "2026-W01", "--statement", str(statement))
    assert code == 0, out + err
    results = out.splitlines()
    assert len(results) == 3
    assert all(line.endswith(": matched") for line in results), out
    assert sorted(line.split()[0] for line in results) == sorted(ACCOUNTS.values())
