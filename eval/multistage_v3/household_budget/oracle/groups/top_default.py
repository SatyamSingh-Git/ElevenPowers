import csv
import io

from budgetbook.cli import main


def bb(capsys, folder, *args):
    code = main(["--dir", str(folder), *args])
    out, err = capsys.readouterr()
    assert code == 0, err
    return out


def test_month_report_lists_ten_payees(tmp_path, capsys):
    folder = tmp_path / "book"
    bb(capsys, folder, "init")
    bb(capsys, folder, "account", "add", "Current")
    for number in range(1, 13):
        bb(capsys, folder, "add", f"2026-03-{number:02d}", "Current", f"SHOP {number:02d}", f"-{number}.00",
           "--category", "Gifts")
    out = bb(capsys, folder, "report", "month", "2026-03", "--format", "csv")
    payees = [row[1:] for row in csv.reader(io.StringIO(out)) if row and row[0] == "Top payees"]
    assert payees == [[f"SHOP {number:02d}", f"{number}.00"] for number in range(12, 2, -1)]
