import csv

from budgetbook.cli import main


def bb(capsys, folder, *args):
    code = main(["--dir", str(folder), *args])
    out, err = capsys.readouterr()
    assert code == 0, err
    return out


def amounts(folder):
    with open(folder / "transactions.csv", newline="", encoding="utf-8") as handle:
        return sorted(row["amount"] for row in csv.DictReader(handle))


def test_added_amounts_are_exact(tmp_path, capsys):
    folder = tmp_path / "book"
    bb(capsys, folder, "init")
    bb(capsys, folder, "account", "add", "Current")
    bb(capsys, folder, "add", "2026-05-02", "Current", "Corner shop", "-19.99")
    bb(capsys, folder, "add", "2026-05-03", "Current", "Bakery", "-0.29")
    assert amounts(folder) == ["-0.29", "-19.99"]


def test_statement_amounts_are_exact(tmp_path, capsys):
    folder = tmp_path / "book"
    bb(capsys, folder, "init")
    bb(capsys, folder, "account", "add", "Current")
    statement = tmp_path / "may.csv"
    statement.write_text("Date,Description,Amount\n2026-05-02,REFUND,4.35\n2026-05-03,TESCO,-19.99\n",
                         encoding="utf-8")
    bb(capsys, folder, "import", "Current", str(statement))
    assert amounts(folder) == ["-19.99", "4.35"]


def test_budget_status_adds_up_exact_amounts(tmp_path, capsys):
    folder = tmp_path / "book"
    bb(capsys, folder, "init")
    bb(capsys, folder, "account", "add", "Current")
    bb(capsys, folder, "budget", "set", "Groceries", "100.00")
    for _ in range(3):
        bb(capsys, folder, "add", "2026-05-02", "Current", "TESCO", "-19.99", "--category", "Groceries")
    out = bb(capsys, folder, "budget", "status", "2026-05", "--format", "csv")
    rows = [row for row in csv.reader(out.splitlines()) if row[:2] == ["Budgets", "Groceries"]]
    assert rows[0][4] == "59.97"
