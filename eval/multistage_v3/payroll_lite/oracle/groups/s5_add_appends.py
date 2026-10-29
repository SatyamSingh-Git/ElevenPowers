"""A row added with `payroll timesheet add` goes at the end of the stored timesheet."""
import csv
import json

from payroll.cli import main

SETTINGS = "[company]\nname = Harbour Bakery\npay_frequency = weekly\nfirst_period_start = 2026-01-05\n"
EMPLOYEES = [
    {"id": "E001", "name": "Ana Lima", "pay_type": "hourly", "rate": "25.00", "bank_account": "11-1111-0000001-00"},
    {"id": "E002", "name": "Ben Okafor", "pay_type": "hourly", "rate": "30.00", "bank_account": "22-2222-0000002-00"},
]


def cli(folder, capsys, *args):
    capsys.readouterr()
    code = main(["--data", str(folder), *args])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def stored(folder):
    with (folder / "timesheets" / "2026-W01.csv").open(newline="", encoding="utf-8") as handle:
        return [(row["employee_id"], row["date"], row["kind"]) for row in csv.DictReader(handle)]


def test_added_rows_go_last(tmp_path, capsys):
    (tmp_path / "payroll.ini").write_text(SETTINGS, encoding="utf-8")
    (tmp_path / "employees.json").write_text(json.dumps({"employees": EMPLOYEES}), encoding="utf-8")
    sheet = tmp_path / "week.csv"
    sheet.write_text("employee_id,date,hours,kind\nE002,2026-01-06,8,work\nE001,2026-01-07,8,work\n",
                     encoding="utf-8")
    code, _, err = cli(tmp_path, capsys, "timesheet", "import", str(sheet), "--period", "2026-W01")
    assert code == 0, err
    code, _, err = cli(tmp_path, capsys, "timesheet", "add", "--period", "2026-W01", "--employee", "E001",
                       "--date", "2026-01-05", "--hours", "3", "--kind", "sick")
    assert code == 0, err
    code, _, err = cli(tmp_path, capsys, "timesheet", "add", "--period", "2026-W01", "--employee", "E002",
                       "--date", "2026-01-05", "--hours", "8")
    assert code == 0, err
    assert stored(tmp_path) == [
        ("E002", "2026-01-06", "work"),
        ("E001", "2026-01-07", "work"),
        ("E001", "2026-01-05", "sick"),
        ("E002", "2026-01-05", "work"),
    ]
