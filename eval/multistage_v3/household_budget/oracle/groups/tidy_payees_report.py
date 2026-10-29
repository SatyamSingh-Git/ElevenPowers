import csv
import io

from budgetbook.cli import main


def bb(capsys, folder, *args):
    code = main(["--dir", str(folder), *args])
    out, err = capsys.readouterr()
    assert code == 0, err
    return out


def test_spellings_of_one_payee_are_one_payee_in_the_report(tmp_path, capsys):
    folder = tmp_path / "book"
    bb(capsys, folder, "init")
    bb(capsys, folder, "account", "add", "Current")
    bb(capsys, folder, "add", "2026-03-02", "Current", "Tesco  Stores", "-10.00", "--category", "Groceries")
    bb(capsys, folder, "add", "2026-03-09", "Current", "TESCO STORES", "-20.00", "--category", "Groceries")
    bb(capsys, folder, "add", "2026-03-16", "Current", "tesco stores", "-30.00", "--category", "Groceries")
    out = bb(capsys, folder, "report", "month", "2026-03", "--format", "csv")
    payees = [row[1:] for row in csv.reader(io.StringIO(out)) if row and row[0] == "Top payees"]
    assert payees == [["TESCO STORES", "60.00"]]
