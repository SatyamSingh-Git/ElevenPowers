import csv

from budgetbook.cli import main

STATEMENT = (
    "Date,Description,Paid in,Paid out,Balance\n"
    "03/04/2026,INTEREST,1.50,,1001.50\n"
    "05/04/2026,TRANSFER TO CURRENT,,200.00,801.50\n"
)


def bb(capsys, folder, *args):
    code = main(["--dir", str(folder), *args])
    out, err = capsys.readouterr()
    assert code == 0, err
    return out


def test_paid_in_out_statement_is_recognised(tmp_path, capsys):
    folder = tmp_path / "book"
    bb(capsys, folder, "init")
    bb(capsys, folder, "account", "add", "Saver", "--kind", "savings")
    statement = tmp_path / "saver.csv"
    statement.write_text(STATEMENT, encoding="utf-8")
    bb(capsys, folder, "import", "Saver", str(statement))
    with open(folder / "transactions.csv", newline="", encoding="utf-8") as handle:
        rows = sorted((row["date"], row["amount"], row["source"]) for row in csv.DictReader(handle))
    assert rows == [("2026-04-03", "1.50", "import:paid_in_out"), ("2026-04-05", "-200.00", "import:paid_in_out")]
