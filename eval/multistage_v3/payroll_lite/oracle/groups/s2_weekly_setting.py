"""overtime.weekly_threshold in payroll.ini; holiday and sick hours do not count toward it."""
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


def paid_hours(folder, capsys, settings, period, rows):
    (folder / "payroll.ini").write_text(settings, encoding="utf-8")
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
    return hours


def test_threshold_from_settings(tmp_path, capsys):
    settings = SETTINGS + "\n[overtime]\nweekly_threshold = 30\n"
    rows = [f"E010,2026-01-{day:02d},8,work" for day in range(5, 10)]
    assert paid_hours(tmp_path, capsys, settings, "2026-W01", rows) == {
        "basic": Decimal("30"), "overtime": Decimal("10")}


def test_holiday_and_sick_hours_do_not_count(tmp_path, capsys):
    rows = [f"E010,2026-01-{day:02d},8,work" for day in (12, 13, 14, 15, 16, 17)] + ["E010,2026-01-18,8,sick"]
    # The 16th is Founders' Day, so the week holds 40 ordinary hours, 8 holiday hours and 8 sick hours.
    assert paid_hours(tmp_path, capsys, SETTINGS, "2026-W02", rows) == {
        "basic": Decimal("40"), "holiday": Decimal("8"), "sick": Decimal("8")}


def test_setting_is_accepted(tmp_path, capsys):
    (tmp_path / "payroll.ini").write_text(SETTINGS + "\n[overtime]\nweekly_threshold = 37.5\n", encoding="utf-8")
    code, _, err = cli(tmp_path, capsys, "periods", "--year", "2026")
    assert code == 0, err
