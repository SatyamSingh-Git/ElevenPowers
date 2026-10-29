import csv
import json

from budgetbook.cli import main

STATEMENT = (
    "Date,Description,Amount\n"
    "2026-03-02,BP 1234 LONDON,-40.00\n"
    "2026-03-03,EBPAY ONLINE,-15.00\n"
    "2026-03-04,BPAY BILLER,-22.00\n"
    "2026-03-05,CARD PAYMENT BP,-30.00\n"
)


def bb(capsys, folder, *args):
    code = main(["--dir", str(folder), *args])
    out, err = capsys.readouterr()
    assert code == 0, err
    return out


def categories(folder):
    with open(folder / "transactions.csv", newline="", encoding="utf-8") as handle:
        return {row["date"]: row["category"] for row in csv.DictReader(handle)}


def test_contains_rule_matches_whole_words_only(tmp_path, capsys):
    folder = tmp_path / "book"
    bb(capsys, folder, "init")
    bb(capsys, folder, "account", "add", "Current")
    bb(capsys, folder, "rule", "add", "contains", "BP", "Fuel")
    statement = tmp_path / "march.csv"
    statement.write_text(STATEMENT, encoding="utf-8")
    bb(capsys, folder, "import", "Current", str(statement))
    assert categories(folder) == {"2026-03-02": "Fuel", "2026-03-03": "", "2026-03-04": "", "2026-03-05": "Fuel"}


def test_contains_rule_from_the_rules_file_when_categorising(tmp_path, capsys):
    folder = tmp_path / "book"
    bb(capsys, folder, "init")
    bb(capsys, folder, "account", "add", "Current")
    statement = tmp_path / "march.csv"
    statement.write_text(STATEMENT, encoding="utf-8")
    bb(capsys, folder, "import", "Current", str(statement))
    (folder / "rules.json").write_text(json.dumps([{"match": "contains", "pattern": "bp", "category": "Fuel"}]),
                                       encoding="utf-8")
    bb(capsys, folder, "categorize")
    assert categories(folder) == {"2026-03-02": "Fuel", "2026-03-03": "", "2026-03-04": "", "2026-03-05": "Fuel"}
