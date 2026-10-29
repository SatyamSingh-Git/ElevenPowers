import csv

from budgetbook.cli import main


def bb(capsys, folder, *args):
    code = main(["--dir", str(folder), *args])
    out, err = capsys.readouterr()
    assert code == 0, err
    return out


def stored_payees(folder):
    with open(folder / "transactions.csv", newline="", encoding="utf-8") as handle:
        return sorted(row["payee"] for row in csv.DictReader(handle))


def test_added_payee_is_stored_upper_case_with_single_spaces(tmp_path, capsys):
    folder = tmp_path / "book"
    bb(capsys, folder, "init")
    bb(capsys, folder, "account", "add", "Current")
    bb(capsys, folder, "add", "2026-03-02", "Current", "Corner   shop  Ltd", "-4.50")
    assert stored_payees(folder) == ["CORNER SHOP LTD"]


def test_imported_payees_are_stored_upper_case_with_single_spaces(tmp_path, capsys):
    folder = tmp_path / "book"
    bb(capsys, folder, "init")
    bb(capsys, folder, "account", "add", "Current")
    statement = tmp_path / "march.csv"
    statement.write_text("Date,Description,Amount\n"
                         "2026-03-02,Tesco  Stores 3297,-20.00\n"
                         "2026-03-03,costa coffee,-3.50\n", encoding="utf-8")
    bb(capsys, folder, "import", "Current", str(statement))
    assert stored_payees(folder) == ["COSTA COFFEE", "TESCO STORES 3297"]
