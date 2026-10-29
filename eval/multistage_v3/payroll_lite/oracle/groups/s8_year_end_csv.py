"""The CSV year-end summary has a periods column after the name."""
import csv
import io
import json

from payroll.cli import main

SETTINGS = "[company]\nname = Harbour Bakery\npay_frequency = weekly\nfirst_period_start = 2026-01-05\n"
EMPLOYEES = [
    {"id": "E001", "name": "Ana Lima", "pay_type": "hourly", "rate": "25.00", "bank_account": "11-1111-0000001-00"},
    {"id": "E003", "name": "Cara Diaz", "pay_type": "salaried", "rate": "52000.00",
     "bank_account": "33-3333-0000003-00"},
]


def cli(folder, capsys, *args):
    capsys.readouterr()
    code = main(["--data", str(folder), *args])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_periods_counts_the_runs_that_paid_each_person(tmp_path, capsys):
    (tmp_path / "payroll.ini").write_text(SETTINGS, encoding="utf-8")
    (tmp_path / "employees.json").write_text(json.dumps({"employees": EMPLOYEES}), encoding="utf-8")
    for period, day in (("2026-W01", "2026-01-05"), ("2026-W02", "2026-01-12")):
        sheet = tmp_path / f"{period}.csv"
        sheet.write_text(f"employee_id,date,hours,kind\nE001,{day},8,work\n", encoding="utf-8")
        code, _, err = cli(tmp_path, capsys, "timesheet", "import", str(sheet), "--period", period)
        assert code == 0, err
        code, _, err = cli(tmp_path, capsys, "run", "--period", period)
        assert code == 0, err
        if period == "2026-W01":
            code, _, err = cli(tmp_path, capsys, "employees", "leave", "E003")
            assert code == 0, err
    code, out, err = cli(tmp_path, capsys, "year-end", "--year", "2026", "--format", "csv")
    assert code == 0, err
    reader = csv.reader(io.StringIO(out))
    assert next(reader) == ["employee_id", "name", "periods", "gross", "tax", "deductions", "net"]
    rows = {row[0]: row for row in reader}
    assert rows["E001"][:4] == ["E001", "Ana Lima", "2", "400.00"]
    assert rows["E003"][:4] == ["E003", "Cara Diaz", "1", "1000.00"]
