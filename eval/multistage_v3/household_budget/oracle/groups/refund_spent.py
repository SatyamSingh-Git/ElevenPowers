import csv
import io

from budgetbook.cli import main


def bb(capsys, folder, *args):
    code = main(["--dir", str(folder), *args])
    out, err = capsys.readouterr()
    assert code == 0, err
    return out


def status(capsys, folder, month):
    out = bb(capsys, folder, "budget", "status", month, "--format", "csv")
    return {row[1]: row[2:6] for row in csv.reader(io.StringIO(out)) if row and row[0] == "Budgets"}


def test_refund_reduces_spent_in_budget_status(tmp_path, capsys):
    folder = tmp_path / "book"
    bb(capsys, folder, "init")
    bb(capsys, folder, "account", "add", "Current")
    bb(capsys, folder, "budget", "set", "Clothing", "100.00")
    bb(capsys, folder, "budget", "set", "Groceries", "400.00")
    bb(capsys, folder, "add", "2026-03-07", "Current", "ZARA", "-80.00", "--category", "Clothing")
    bb(capsys, folder, "add", "2026-03-21", "Current", "ZARA", "30.00", "--category", "Clothing")
    bb(capsys, folder, "add", "2026-03-02", "Current", "TESCO", "-120.50", "--category", "Groceries")
    march = status(capsys, folder, "2026-03")
    assert march["Clothing"] == ["100.00", "0.00", "50.00", "50.00"]
    assert march["Groceries"] == ["400.00", "0.00", "120.50", "279.50"]
