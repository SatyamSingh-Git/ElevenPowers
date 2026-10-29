"""The text year-end summary has a periods column after the name."""
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


def test_text_columns(tmp_path, capsys):
    (tmp_path / "payroll.ini").write_text(SETTINGS, encoding="utf-8")
    (tmp_path / "employees.json").write_text(json.dumps({"employees": EMPLOYEES}), encoding="utf-8")
    for period, day in (("2026-W01", "2026-01-05"), ("2026-W02", "2026-01-12"), ("2026-W03", "2026-01-19")):
        sheet = tmp_path / f"{period}.csv"
        sheet.write_text(f"employee_id,date,hours,kind\nE001,{day},8,work\n", encoding="utf-8")
        code, _, err = cli(tmp_path, capsys, "timesheet", "import", str(sheet), "--period", period)
        assert code == 0, err
        code, _, err = cli(tmp_path, capsys, "run", "--period", period)
        assert code == 0, err
    code, out, err = cli(tmp_path, capsys, "year-end", "--year", "2026")
    assert code == 0, err
    lines = out.splitlines()
    header = next(line.split() for line in lines if line.split()[:1] == ["employee_id"])
    assert header == ["employee_id", "name", "periods", "gross", "tax", "deductions", "net"]
    row = next(line.split() for line in lines if line.split()[:1] == ["E001"])
    assert row[:5] == ["E001", "Ana", "Lima", "3", "600.00"]
