"""Pay-run files carry schema 2 and write every total as integer cents."""
import json

import pytest

from payroll.cli import main

SETTINGS = "[company]\nname = Harbour Bakery\npay_frequency = weekly\nfirst_period_start = 2026-01-05\n"
EMPLOYEES = [
    {"id": "E001", "name": "Ana Lima", "pay_type": "hourly", "rate": "25.00",
     "bank_account": "11-1111-0000001-00",
     "deductions": [{"kind": "percent", "label": "Pension", "rate": "5"}]},
]
ROWS = ["E001,2026-01-05,8,work", "E001,2026-01-06,9,work", "E001,2026-01-07,8,work",
        "E001,2026-01-08,7.5,work", "E001,2026-01-09,7.5,work"]


def cli(folder, capsys, *args):
    capsys.readouterr()
    code = main(["--data", str(folder), *args])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


@pytest.fixture
def run_file(tmp_path, capsys):
    (tmp_path / "payroll.ini").write_text(SETTINGS, encoding="utf-8")
    (tmp_path / "employees.json").write_text(json.dumps({"employees": EMPLOYEES}), encoding="utf-8")
    sheet = tmp_path / "week.csv"
    sheet.write_text("employee_id,date,hours,kind\n" + "\n".join(ROWS) + "\n", encoding="utf-8")
    code, _, err = cli(tmp_path, capsys, "timesheet", "import", str(sheet), "--period", "2026-W01")
    assert code == 0, err
    code, _, err = cli(tmp_path, capsys, "run", "--period", "2026-W01")
    assert code == 0, err
    return json.loads((tmp_path / "runs" / "2026-W01.json").read_text(encoding="utf-8"))


def is_whole(value):
    return type(value) is int


def test_schema_is_2(run_file):
    assert run_file["schema"] == 2


def test_payslip_totals_are_integer_cents(run_file):
    slip = run_file["payslips"][0]
    totals = {name: slip[name] for name in ("gross", "tax", "deductions", "net")}
    assert all(is_whole(value) for value in totals.values()), totals
    assert totals == {"gross": 101250, "tax": 13933, "deductions": 5063, "net": 82254}


def test_run_totals_are_integer_cents(run_file):
    totals = run_file["totals"]
    assert all(is_whole(totals[name]) for name in ("gross", "tax", "deductions", "net")), totals
    assert (totals["gross"], totals["net"]) == (101250, 82254)
