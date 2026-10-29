"""Bank file rows are account, reference, amount, name."""
import csv
import json

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


def test_default_bank_file(tmp_path, capsys):
    (tmp_path / "payroll.ini").write_text(SETTINGS, encoding="utf-8")
    (tmp_path / "employees.json").write_text(json.dumps({"employees": EMPLOYEES}), encoding="utf-8")
    sheet = tmp_path / "week.csv"
    sheet.write_text("employee_id,date,hours,kind\n" + "\n".join(ROWS) + "\n", encoding="utf-8")
    for args in (("timesheet", "import", str(sheet), "--period", "2026-W01"), ("run", "--period", "2026-W01"),
                 ("bank-file", "--period", "2026-W01")):
        code, _, err = cli(tmp_path, capsys, *args)
        assert code == 0, err
    with (tmp_path / "bank" / "2026-W01.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert rows == [["11-1111-0000001-00", "PAY 2026-W01", "822.54", "Ana Lima"]]
