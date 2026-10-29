"""percent_over takes nothing at or below the threshold, and sits beside other deductions."""
import json

from payroll.cli import main

SETTINGS = "[company]\nname = Harbour Bakery\npay_frequency = weekly\nfirst_period_start = 2026-01-05\n"
LOAN = {"kind": "percent_over", "label": "Student loan", "rate": "12", "threshold": "400.00"}
EMPLOYEES = [
    {"id": "E021", "name": "Fay Moss", "pay_type": "hourly", "rate": "25.00",
     "bank_account": "21-2121-0000021-00",
     "deductions": [LOAN, {"kind": "percent", "label": "Pension", "rate": "5"}]},
    {"id": "E022", "name": "Gus Hale", "pay_type": "hourly", "rate": "25.00",
     "bank_account": "22-2121-0000022-00",
     "deductions": [LOAN]},
]
ROWS = ["E021,2026-01-05,8,work", "E021,2026-01-06,4,work", "E022,2026-01-05,8,work", "E022,2026-01-06,8,work"]


def cli(folder, capsys, *args):
    capsys.readouterr()
    code = main(["--data", str(folder), *args])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_nothing_taken_at_or_below_the_threshold(tmp_path, capsys):
    (tmp_path / "payroll.ini").write_text(SETTINGS, encoding="utf-8")
    (tmp_path / "employees.json").write_text(json.dumps({"employees": EMPLOYEES}), encoding="utf-8")
    sheet = tmp_path / "week.csv"
    sheet.write_text("employee_id,date,hours,kind\n" + "\n".join(ROWS) + "\n", encoding="utf-8")
    code, _, err = cli(tmp_path, capsys, "timesheet", "import", str(sheet), "--period", "2026-W01")
    assert code == 0, err
    code, _, err = cli(tmp_path, capsys, "run", "--period", "2026-W01")
    assert code == 0, err

    document = json.loads((tmp_path / "runs" / "2026-W01.json").read_text(encoding="utf-8"))
    slips = {slip["employee_id"]: slip for slip in document["payslips"]}
    # E021: gross 300.00, below the threshold, so only the 5% pension comes off.
    assert (slips["E021"]["gross"], slips["E021"]["deductions"], slips["E021"]["net"]) == (30000, 1500, 27462)
    # E022: gross exactly 400.00.
    assert (slips["E022"]["gross"], slips["E022"]["deductions"], slips["E022"]["net"]) == (40000, 0, 37462)
