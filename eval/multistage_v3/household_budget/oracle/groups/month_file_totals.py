import json

from budgetbook.cli import main


def bb(capsys, folder, *args):
    code = main(["--dir", str(folder), *args])
    out, err = capsys.readouterr()
    assert code == 0, err
    return out


def test_month_file_totals_are_decimal_strings(tmp_path, capsys):
    folder = tmp_path / "book"
    bb(capsys, folder, "init")
    bb(capsys, folder, "account", "add", "Current")
    bb(capsys, folder, "add", "2026-03-01", "Current", "ACME LTD", "2500.00", "--category", "Salary")
    bb(capsys, folder, "add", "2026-03-02", "Current", "TESCO", "-382.50", "--category", "Groceries")
    bb(capsys, folder, "add", "2026-03-05", "Current", "CINEMA", "-12.50", "--category", "Entertainment")
    bb(capsys, folder, "close", "2026-03")
    data = json.loads((folder / "closed" / "2026-03.json").read_text(encoding="utf-8"))
    assert data["format"] == 2
    assert data["income"] == "2500.00"
    assert data["spending"] == "395.00"
