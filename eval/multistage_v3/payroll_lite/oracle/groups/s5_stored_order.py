"""The stored timesheet keeps the rows in the order of the uploaded file."""
import csv
import json

import pytest

from payroll.cli import main

SETTINGS = "[company]\nname = Harbour Bakery\npay_frequency = weekly\nfirst_period_start = 2026-01-05\n"
EMPLOYEES = [
    {"id": "E001", "name": "Ana Lima", "pay_type": "hourly", "rate": "25.00", "bank_account": "11-1111-0000001-00"},
    {"id": "E002", "name": "Ben Okafor", "pay_type": "hourly", "rate": "30.00", "bank_account": "22-2222-0000002-00"},
]
UPLOAD = [
    ("E002", "2026-01-07", "8.00", "work"),
    ("E001", "2026-01-07", "6.00", "work"),
    ("E002", "2026-01-05", "4.00", "sick"),
    ("E001", "2026-01-06", "7.50", "work"),
    ("E002", "2026-01-06", "8.00", "work"),
    ("E001", "2026-01-05", "8.00", "work"),
]


def cli(folder, capsys, *args):
    capsys.readouterr()
    code = main(["--data", str(folder), *args])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


@pytest.fixture
def books(tmp_path, capsys):
    (tmp_path / "payroll.ini").write_text(SETTINGS, encoding="utf-8")
    (tmp_path / "employees.json").write_text(json.dumps({"employees": EMPLOYEES}), encoding="utf-8")
    sheet = tmp_path / "week.csv"
    sheet.write_text("employee_id,date,hours,kind\n" + "".join(",".join(row) + "\n" for row in UPLOAD),
                     encoding="utf-8")
    code, _, err = cli(tmp_path, capsys, "timesheet", "import", str(sheet), "--period", "2026-W01")
    assert code == 0, err
    return tmp_path


def test_stored_file_is_in_upload_order(books):
    with (books / "timesheets" / "2026-W01.csv").open(newline="", encoding="utf-8") as handle:
        stored = [(row["employee_id"], row["date"], row["kind"]) for row in csv.DictReader(handle)]
    assert stored == [(employee, day, kind) for employee, day, _, kind in UPLOAD]


def test_show_prints_upload_order(books, capsys):
    code, out, err = cli(books, capsys, "timesheet", "show", "--period", "2026-W01")
    assert code == 0, err
    shown = [line.split()[:2] for line in out.splitlines() if line.split()[:1] in (["E001"], ["E002"])]
    assert shown == [[employee, day] for employee, day, _, _ in UPLOAD]
