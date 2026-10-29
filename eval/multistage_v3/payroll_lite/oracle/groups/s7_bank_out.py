"""The new bank layout also holds for --out, several payments and long names."""
import csv
import json

from payroll.cli import main

SETTINGS = "[company]\nname = Harbour Bakery\npay_frequency = weekly\nfirst_period_start = 2026-01-05\n"
EMPLOYEES = [
    {"id": "E003", "name": "Cara Diaz", "pay_type": "salaried", "rate": "52000.00",
     "bank_account": "33-3333-0000003-00"},
    {"id": "E004", "name": "Bartholomew Okonkwo-Smith", "pay_type": "salaried", "rate": "26000.00",
     "bank_account": "44-4444-0000004-00"},
]


def cli(folder, capsys, *args):
    capsys.readouterr()
    code = main(["--data", str(folder), *args])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_custom_path_and_long_names(tmp_path, capsys):
    (tmp_path / "payroll.ini").write_text(SETTINGS, encoding="utf-8")
    (tmp_path / "employees.json").write_text(json.dumps({"employees": EMPLOYEES}), encoding="utf-8")
    out_file = tmp_path / "upload" / "payments.csv"
    for args in (("run", "--period", "2026-W02"), ("bank-file", "--period", "2026-W02", "--out", str(out_file))):
        code, _, err = cli(tmp_path, capsys, *args)
        assert code == 0, err
    with out_file.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    # Salaries of 1,000.00 and 500.00 a week, after tax.
    assert rows == [
        ["33-3333-0000003-00", "PAY 2026-W02", "864.42", "Cara Diaz"],
        ["44-4444-0000004-00", "PAY 2026-W02", "459.62", "Bartholomew Okonkwo-"],
    ]
