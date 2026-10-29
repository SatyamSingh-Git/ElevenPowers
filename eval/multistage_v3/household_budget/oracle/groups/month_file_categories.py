import json

from budgetbook.cli import main


def bb(capsys, folder, *args):
    code = main(["--dir", str(folder), *args])
    out, err = capsys.readouterr()
    assert code == 0, err
    return out


def test_month_file_category_amounts_are_decimal_strings(tmp_path, capsys):
    folder = tmp_path / "book"
    bb(capsys, folder, "init")
    bb(capsys, folder, "account", "add", "Current")
    bb(capsys, folder, "budget", "set", "Groceries", "400.00", "--rollover")
    bb(capsys, folder, "budget", "set", "Eating out", "50.00")
    bb(capsys, folder, "add", "2026-02-02", "Current", "TESCO", "-350.00", "--category", "Groceries")
    bb(capsys, folder, "add", "2026-03-02", "Current", "TESCO", "-382.50", "--category", "Groceries")
    bb(capsys, folder, "add", "2026-03-09", "Current", "PIZZA PLACE", "-62.50", "--category", "Eating out")
    bb(capsys, folder, "close", "2026-02")
    bb(capsys, folder, "close", "2026-03")
    data = json.loads((folder / "closed" / "2026-03.json").read_text(encoding="utf-8"))
    entries = {entry["name"]: entry for entry in data["categories"]}
    assert entries["Groceries"] == {"name": "Groceries", "group": "essentials", "budget": "400.00",
                                    "carried": "50.00", "spent": "382.50", "remaining": "67.50"}
    assert entries["Eating out"] == {"name": "Eating out", "group": "lifestyle", "budget": "50.00",
                                     "carried": "0.00", "spent": "62.50", "remaining": "-12.50"}
