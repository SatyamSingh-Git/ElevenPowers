"""Percentage deductions do not apply to per_shift allowances; fixed allowances stay in gross pay."""
import json

from payroll.cli import main

SETTINGS = "[company]\nname = Harbour Bakery\npay_frequency = weekly\nfirst_period_start = 2026-01-05\n"
EMPLOYEES = [
    {"id": "E031", "name": "Ivo Reyes", "pay_type": "hourly", "rate": "30.00",
     "bank_account": "31-3131-0000031-00",
     "allowances": [{"kind": "per_shift", "label": "Meal", "amount": "8.00"},
                    {"kind": "fixed", "label": "Tools", "amount": "20.00"}],
     "deductions": [{"kind": "percent", "label": "Pension", "rate": "5"}]},
]


def cli(folder, capsys, *args):
    capsys.readouterr()
    code = main(["--data", str(folder), *args])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_pension_on_wages_and_fixed_allowance_only(tmp_path, capsys):
    (tmp_path / "payroll.ini").write_text(SETTINGS, encoding="utf-8")
    (tmp_path / "employees.json").write_text(json.dumps({"employees": EMPLOYEES}), encoding="utf-8")
    sheet = tmp_path / "week.csv"
    rows = [f"E031,2026-01-{day:02d},8,work" for day in range(5, 9)]
    sheet.write_text("employee_id,date,hours,kind\n" + "\n".join(rows) + "\n", encoding="utf-8")
    code, _, err = cli(tmp_path, capsys, "timesheet", "import", str(sheet), "--period", "2026-W01")
    assert code == 0, err
    code, _, err = cli(tmp_path, capsys, "run", "--period", "2026-W01")
    assert code == 0, err
    slip = json.loads((tmp_path / "runs" / "2026-W01.json").read_text(encoding="utf-8"))["payslips"][0]
    # Wages 960.00 plus the fixed 20.00; four shifts of meal money (32.00) outside gross.
    assert slip["gross"] == 98000
    assert slip["deductions"] == 4900
    assert slip["tax"] == 12958
    assert slip["net"] == 98000 - 12958 - 4900 + 3200
