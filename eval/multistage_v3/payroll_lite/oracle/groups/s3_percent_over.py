"""Deduction kind percent_over takes rate percent of the gross pay above threshold."""
import json
from decimal import Decimal

from payroll.cli import main

SETTINGS = "[company]\nname = Harbour Bakery\npay_frequency = weekly\nfirst_period_start = 2026-01-05\n"
EMPLOYEES = [
    {"id": "E020", "name": "Eli Stone", "pay_type": "hourly", "rate": "25.00",
     "bank_account": "20-2020-0000020-00",
     "deductions": [{"kind": "percent_over", "label": "Student loan", "rate": "12", "threshold": "400.00"}]},
]


def cli(folder, capsys, *args):
    capsys.readouterr()
    code = main(["--data", str(folder), *args])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_deducts_twelve_percent_of_gross_above_400(tmp_path, capsys):
    (tmp_path / "payroll.ini").write_text(SETTINGS, encoding="utf-8")
    (tmp_path / "employees.json").write_text(json.dumps({"employees": EMPLOYEES}), encoding="utf-8")
    sheet = tmp_path / "week.csv"
    rows = [f"E020,2026-01-{day:02d},8,work" for day in range(5, 10)]
    sheet.write_text("employee_id,date,hours,kind\n" + "\n".join(rows) + "\n", encoding="utf-8")
    code, _, err = cli(tmp_path, capsys, "timesheet", "import", str(sheet), "--period", "2026-W01")
    assert code == 0, err
    code, _, err = cli(tmp_path, capsys, "run", "--period", "2026-W01")
    assert code == 0, err

    slip = json.loads((tmp_path / "runs" / "2026-W01.json").read_text(encoding="utf-8"))["payslips"][0]
    # Gross 1,000.00; 12% of the 600.00 above the threshold.
    assert slip["deductions"] == 7200
    assert slip["net"] == 100000 - 13558 - 7200

    code, out, err = cli(tmp_path, capsys, "payslip", "--period", "2026-W01", "--employee", "E020")
    assert code == 0, err
    loan = [line for line in out.splitlines() if line.strip().startswith("Student loan")]
    assert len(loan) == 1 and loan[0].split()[-1] == "72.00"
    net = next(line for line in out.splitlines() if line.startswith("Net pay"))
    assert Decimal(net.split()[-1].replace(",", "")) == Decimal("792.42")
