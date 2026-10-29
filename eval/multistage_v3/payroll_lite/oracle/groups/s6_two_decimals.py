"""Every figure in `payroll hours` has two decimal places."""
import json

from payroll.cli import main

SETTINGS = "[company]\nname = Harbour Bakery\npay_frequency = weekly\nfirst_period_start = 2026-01-05\n"
EMPLOYEES = [
    {"id": "E001", "name": "Ana Lima", "pay_type": "hourly", "rate": "25.00", "bank_account": "11-1111-0000001-00"},
]


def cli(folder, capsys, *args):
    capsys.readouterr()
    code = main(["--data", str(folder), *args])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_every_column_has_two_decimals(tmp_path, capsys):
    (tmp_path / "payroll.ini").write_text(SETTINGS, encoding="utf-8")
    (tmp_path / "employees.json").write_text(json.dumps({"employees": EMPLOYEES}), encoding="utf-8")
    sheet = tmp_path / "week.csv"
    sheet.write_text("employee_id,date,hours,kind\nE001,2026-01-05,9.75,work\n", encoding="utf-8")
    code, _, err = cli(tmp_path, capsys, "timesheet", "import", str(sheet), "--period", "2026-W01")
    assert code == 0, err
    code, out, err = cli(tmp_path, capsys, "hours", "--period", "2026-W01")
    assert code == 0, err
    rows = {line.split()[0]: line.split()[1:] for line in out.splitlines() if line.split()[:1] in (["E001"], ["total"])}
    assert rows["E001"] == ["8.00", "1.75", "0.00", "0.00", "9.75"]
    assert rows["total"] == ["8.00", "1.75", "0.00", "0.00", "9.75"]
