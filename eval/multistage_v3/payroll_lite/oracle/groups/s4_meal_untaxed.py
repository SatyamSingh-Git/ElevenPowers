"""per_shift allowances are left out of gross pay and tax, and added to net pay."""
import json

from payroll.cli import main

SETTINGS = "[company]\nname = Harbour Bakery\npay_frequency = weekly\nfirst_period_start = 2026-01-05\n"
EMPLOYEES = [
    {"id": "E030", "name": "Hana Cole", "pay_type": "hourly", "rate": "30.00",
     "bank_account": "30-3030-0000030-00",
     "allowances": [{"kind": "per_shift", "label": "Meal", "amount": "8.00"}],
     "deductions": [{"kind": "fixed", "label": "Union", "amount": "12.00"}]},
]


def cli(folder, capsys, *args):
    capsys.readouterr()
    code = main(["--data", str(folder), *args])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_meal_money_is_not_taxed(tmp_path, capsys):
    (tmp_path / "payroll.ini").write_text(SETTINGS, encoding="utf-8")
    (tmp_path / "employees.json").write_text(json.dumps({"employees": EMPLOYEES}), encoding="utf-8")
    sheet = tmp_path / "week.csv"
    rows = [f"E030,2026-01-{day:02d},8,work" for day in range(5, 10)]
    sheet.write_text("employee_id,date,hours,kind\n" + "\n".join(rows) + "\n", encoding="utf-8")
    code, _, err = cli(tmp_path, capsys, "timesheet", "import", str(sheet), "--period", "2026-W01")
    assert code == 0, err
    code, _, err = cli(tmp_path, capsys, "run", "--period", "2026-W01")
    assert code == 0, err
    slip = json.loads((tmp_path / "runs" / "2026-W01.json").read_text(encoding="utf-8"))["payslips"][0]
    # 40 hours at 30.00; five shifts of meal money (40.00) paid on top.
    assert slip["gross"] == 120000
    assert slip["tax"] == 19558
    assert slip["deductions"] == 1200
    assert slip["net"] == 120000 - 19558 - 1200 + 4000
