import csv
import json

from budgetbook.cli import main

STATEMENT = (
    "Date,Description,Amount\n"
    "2026-03-02,BP 1234 LONDON,-40.00\n"
    "2026-03-03,EBPAY ONLINE,-15.00\n"
    "2026-03-04,TESCO STORES,-22.00\n"
)


def bb(capsys, folder, *args):
    code = main(["--dir", str(folder), *args])
    out, err = capsys.readouterr()
    assert code == 0, err
    return out


def categories(folder):
    with open(folder / "transactions.csv", newline="", encoding="utf-8") as handle:
        return {row["date"]: row["category"] for row in csv.DictReader(handle)}


def test_anywhere_rule_matches_inside_words(tmp_path, capsys):
    folder = tmp_path / "book"
    bb(capsys, folder, "init")
    bb(capsys, folder, "account", "add", "Current")
    (folder / "rules.json").write_text(json.dumps([{"match": "anywhere", "pattern": "bp", "category": "Fuel"}]),
                                       encoding="utf-8")
    statement = tmp_path / "march.csv"
    statement.write_text(STATEMENT, encoding="utf-8")
    bb(capsys, folder, "import", "Current", str(statement))
    assert categories(folder) == {"2026-03-02": "Fuel", "2026-03-03": "Fuel", "2026-03-04": ""}


def test_anywhere_rule_can_be_added_from_the_command_line(tmp_path, capsys):
    folder = tmp_path / "book"
    bb(capsys, folder, "init")
    bb(capsys, folder, "account", "add", "Current")
    bb(capsys, folder, "rule", "add", "anywhere", "ESC", "Groceries")
    statement = tmp_path / "march.csv"
    statement.write_text(STATEMENT, encoding="utf-8")
    bb(capsys, folder, "import", "Current", str(statement))
    assert categories(folder)["2026-03-04"] == "Groceries"
