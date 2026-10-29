"""Ordinary hours beyond 40 in a Monday-to-Sunday week are paid as overtime."""
import json
from decimal import Decimal

from payroll.cli import main

SETTINGS = "[company]\nname = Harbour Bakery\npay_frequency = weekly\nfirst_period_start = 2026-01-05\n"
EMPLOYEES = [
    {"id": "E010", "name": "Dee Park", "pay_type": "hourly", "rate": "20.00",
     "bank_account": "10-1010-0000010-00"},
]


def cli(folder, capsys, *args):
    capsys.readouterr()
    code = main(["--data", str(folder), *args])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def pay(folder, capsys, period, rows):
    """(hours by line kind, gross pay on the payslip) for a week of E010's hours."""
    (folder / "payroll.ini").write_text(SETTINGS, encoding="utf-8")
    (folder / "employees.json").write_text(json.dumps({"employees": EMPLOYEES}), encoding="utf-8")
    sheet = folder / f"{period}.csv"
    sheet.write_text("employee_id,date,hours,kind\n" + "\n".join(rows) + "\n", encoding="utf-8")
    code, _, err = cli(folder, capsys, "timesheet", "import", str(sheet), "--period", period)
    assert code == 0, err
    code, _, err = cli(folder, capsys, "run", "--period", period)
    assert code == 0, err
    document = json.loads((folder / "runs" / f"{period}.json").read_text(encoding="utf-8"))
    hours = {}
    for line in document["payslips"][0]["lines"]:
        if line["hours"] is not None:
            hours[line["kind"]] = hours.get(line["kind"], Decimal(0)) + Decimal(line["hours"])
    code, out, err = cli(folder, capsys, "payslip", "--period", period, "--employee", "E010")
    assert code == 0, err
    gross = next(Decimal(line.split()[-1].replace(",", "")) for line in out.splitlines()
                 if line.startswith("Gross pay"))
    return hours, gross


def test_six_eight_hour_days(tmp_path, capsys):
    rows = [f"E010,2026-01-{day:02d},8,work" for day in range(5, 11)]
    hours, gross = pay(tmp_path, capsys, "2026-W01", rows)
    assert hours == {"basic": Decimal("40"), "overtime": Decimal("8")}
    assert gross == Decimal("1040.00")


def test_daily_overtime_is_not_counted_twice(tmp_path, capsys):
    rows = ["E010,2026-01-19,10,work"] + [f"E010,2026-01-{day:02d},8,work" for day in range(20, 25)]
    hours, gross = pay(tmp_path, capsys, "2026-W03", rows)
    assert hours == {"basic": Decimal("40"), "overtime": Decimal("10")}
    assert gross == Decimal("1100.00")
