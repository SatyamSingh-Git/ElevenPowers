import csv

from budgetbook.cli import main


def bb(capsys, folder, *args):
    code = main(["--dir", str(folder), *args])
    out, err = capsys.readouterr()
    return code, out, err


def stored(folder):
    path = folder / "transactions.csv"
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as handle:
        return [row["amount"] for row in csv.DictReader(handle)]


def test_add_refuses_three_decimal_places(tmp_path, capsys):
    folder = tmp_path / "book"
    bb(capsys, folder, "init")
    bb(capsys, folder, "account", "add", "Current")
    code, _, err = bb(capsys, folder, "add", "2026-05-02", "Current", "Corner shop", "10.005")
    assert code == 1
    assert "invalid amount: 10.005" in err
    assert stored(folder) == []


def test_statement_row_with_three_decimal_places_is_skipped(tmp_path, capsys):
    folder = tmp_path / "book"
    bb(capsys, folder, "init")
    bb(capsys, folder, "account", "add", "Current")
    statement = tmp_path / "may.csv"
    statement.write_text("Date,Description,Amount\n2026-05-02,FX PAYMENT,-10.005\n2026-05-03,TESCO,-20.00\n",
                         encoding="utf-8")
    code, _, err = bb(capsys, folder, "import", "Current", str(statement))
    assert code == 0
    assert "invalid amount: -10.005" in err
    assert stored(folder) == ["-20.00"]
