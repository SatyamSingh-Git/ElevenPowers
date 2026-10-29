import csv

from budgetbook.cli import main

APRIL = "Date,Description,Amount\n2026-04-02,TESCO,-60.00\n2026-04-05,ACME LTD,2500.00\n"
MARCH = "Date,Description,Amount\n2026-03-02,TESCO,-120.50\n2026-03-28,COSTA COFFEE,-3.25\n"


def bb(capsys, folder, *args):
    code = main(["--dir", str(folder), *args])
    out, err = capsys.readouterr()
    assert code == 0, err
    return out


def rows(folder):
    with open(folder / "transactions.csv", newline="", encoding="utf-8") as handle:
        return [(row["id"], row["date"]) for row in csv.DictReader(handle)]


def test_later_imports_go_to_the_end_of_the_file(tmp_path, capsys):
    folder = tmp_path / "book"
    bb(capsys, folder, "init")
    bb(capsys, folder, "account", "add", "Current")
    for name, text in (("april.csv", APRIL), ("march.csv", MARCH)):
        statement = tmp_path / name
        statement.write_text(text, encoding="utf-8")
        bb(capsys, folder, "import", "Current", str(statement))
    bb(capsys, folder, "add", "2026-01-15", "Current", "DENTIST", "-45.00")
    assert rows(folder) == [("1", "2026-04-02"), ("2", "2026-04-05"), ("3", "2026-03-02"),
                            ("4", "2026-03-28"), ("5", "2026-01-15")]
