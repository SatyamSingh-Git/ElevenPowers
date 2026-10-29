import csv

from budgetbook.cli import main


def bb(capsys, folder, *args):
    code = main(["--dir", str(folder), *args])
    out, err = capsys.readouterr()
    assert code == 0, err
    return out


def dates(folder):
    with open(folder / "transactions.csv", newline="", encoding="utf-8") as handle:
        return [row["date"] for row in csv.DictReader(handle)]


def test_rewriting_the_file_keeps_the_order_added(tmp_path, capsys):
    folder = tmp_path / "book"
    bb(capsys, folder, "init")
    bb(capsys, folder, "account", "add", "Current")
    bb(capsys, folder, "add", "2026-04-02", "Current", "TESCO", "-60.00")
    bb(capsys, folder, "add", "2026-03-02", "Current", "TESCO", "-120.50")
    bb(capsys, folder, "add", "2026-03-20", "Current", "ZARA", "-80.00")
    bb(capsys, folder, "rule", "add", "contains", "TESCO", "Groceries")
    bb(capsys, folder, "categorize")
    bb(capsys, folder, "file", "3", "Clothing")
    assert dates(folder) == ["2026-04-02", "2026-03-02", "2026-03-20"]
