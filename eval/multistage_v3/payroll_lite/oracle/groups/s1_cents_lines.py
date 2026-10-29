"""Pay-run file lines write amount and rate as integer cents; hours stay as they were."""
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
def lines(tmp_path, capsys):
    (tmp_path / "payroll.ini").write_text(SETTINGS, encoding="utf-8")
    (tmp_path / "employees.json").write_text(json.dumps({"employees": EMPLOYEES}), encoding="utf-8")
    sheet = tmp_path / "week.csv"
    sheet.write_text("employee_id,date,hours,kind\n" + "\n".join(ROWS) + "\n", encoding="utf-8")
    code, _, err = cli(tmp_path, capsys, "timesheet", "import", str(sheet), "--period", "2026-W01")
    assert code == 0, err
    code, _, err = cli(tmp_path, capsys, "run", "--period", "2026-W01")
    assert code == 0, err
    document = json.loads((tmp_path / "runs" / "2026-W01.json").read_text(encoding="utf-8"))
    return {line["kind"]: line for line in document["payslips"][0]["lines"]}


def test_wage_lines_in_cents(lines):
    basic, overtime = lines["basic"], lines["overtime"]
    assert (type(basic["amount"]), type(basic["rate"])) == (int, int)
    assert (basic["amount"], basic["rate"]) == (97500, 2500)
    assert (type(overtime["amount"]), type(overtime["rate"])) == (int, int)
    assert (overtime["amount"], overtime["rate"]) == (3750, 3750)


def test_deduction_line_in_cents(lines):
    assert type(lines["deduction"]["amount"]) is int
    assert lines["deduction"]["amount"] == 5063


def test_hours_unchanged(lines):
    assert (lines["basic"]["hours"], lines["overtime"]["hours"]) == ("39.00", "1.00")
