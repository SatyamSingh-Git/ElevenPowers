import csv
import io

from budgetbook.cli import main

MARCH = (
    "Date,Description,Amount\n"
    "2026-03-02,CARD PAYMENT TO  TESCO STORES 3297,-120.50\n"
    "2026-03-04,SHELL OIL 4021,-40.00\n"
    "2026-03-28,COSTA  COFFEE,-3.25\n"
)
APRIL = (
    "Date,Description,Amount\n"
    "2026-04-01,CARD PAYMENT TO  TESCO STORES 3297,-60.00\n"
    "2026-04-03,SHELL OIL 4021,-45.00\n"
    "2026-04-05,ACME LTD SALARY,2500.00\n"
)


def bb(capsys, folder, *args):
    code = main(["--dir", str(folder), *args])
    out, err = capsys.readouterr()
    return code, out, err


def setup(tmp_path, capsys):
    folder = tmp_path / "book"
    assert bb(capsys, folder, "init")[0] == 0
    assert bb(capsys, folder, "account", "add", "Current", "--opening", "1000.00")[0] == 0
    return folder


def statement(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return str(path)


def stored(folder):
    with open(folder / "transactions.csv", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def section(out, title):
    return [row[1:] for row in csv.reader(io.StringIO(out)) if row and row[0] == title]


def test_reimporting_a_statement_adds_nothing(tmp_path, capsys):
    folder = setup(tmp_path, capsys)
    march = statement(tmp_path, "march.csv", MARCH)
    assert bb(capsys, folder, "import", "Current", march)[0] == 0
    assert len(stored(folder)) == 3
    assert bb(capsys, folder, "import", "Current", march)[0] == 0
    assert len(stored(folder)) == 3
    overlap = statement(tmp_path, "overlap.csv", MARCH + "2026-03-30,BAKERY,-2.50\n")
    assert bb(capsys, folder, "import", "Current", overlap)[0] == 0
    assert len(stored(folder)) == 4


def test_rules_file_imported_rows(tmp_path, capsys):
    folder = setup(tmp_path, capsys)
    assert bb(capsys, folder, "rule", "add", "contains", "TESCO", "Groceries")[0] == 0
    assert bb(capsys, folder, "rule", "add", "prefix", "SHELL", "Fuel")[0] == 0
    assert bb(capsys, folder, "import", "Current", statement(tmp_path, "march.csv", MARCH))[0] == 0
    code, out, _ = bb(capsys, folder, "search", "--category", "Groceries", "--format", "csv")
    assert code == 0
    rows = section(out, "Results")
    assert len(rows) == 1
    assert "TESCO STORES" in rows[0][3].upper()
    code, out, _ = bb(capsys, folder, "search", "--category", "Fuel", "--format", "csv")
    assert [row[5] for row in section(out, "Results")] == ["-40.00"]


def test_search_finds_text_inside_a_payee(tmp_path, capsys):
    folder = setup(tmp_path, capsys)
    assert bb(capsys, folder, "import", "Current", statement(tmp_path, "march.csv", MARCH))[0] == 0
    code, out, _ = bb(capsys, folder, "search", "--payee", "tesc", "--format", "csv")
    assert code == 0
    assert [row[5] for row in section(out, "Results")] == ["-120.50"]
    code, out, _ = bb(capsys, folder, "search", "--payee", "OFFEE", "--format", "csv")
    assert [row[5] for row in section(out, "Results")] == ["-3.25"]


def test_register_runs_in_date_order(tmp_path, capsys):
    folder = setup(tmp_path, capsys)
    assert bb(capsys, folder, "import", "Current", statement(tmp_path, "april.csv", APRIL))[0] == 0
    assert bb(capsys, folder, "import", "Current", statement(tmp_path, "march.csv", MARCH))[0] == 0
    code, out, _ = bb(capsys, folder, "register", "Current", "--format", "csv")
    assert code == 0
    rows = section(out, "Transactions")
    assert [row[0] for row in rows] == ["2026-03-02", "2026-03-04", "2026-03-28",
                                        "2026-04-01", "2026-04-03", "2026-04-05"]
    assert [row[-1] for row in rows] == ["879.50", "839.50", "836.25", "776.25", "731.25", "3231.25"]
    code, out, _ = bb(capsys, folder, "register", "Current", "--month", "2026-04", "--format", "csv")
    assert [row[-1] for row in section(out, "Transactions")] == ["776.25", "731.25", "3231.25"]
