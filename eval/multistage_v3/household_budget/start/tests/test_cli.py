import csv
import io

from budgetbook.cli import main


def run(capsys, folder, *args):
    code = main(["--dir", str(folder), *args])
    out, err = capsys.readouterr()
    return code, out, err


def test_init_then_add_and_search(tmp_path, capsys):
    folder = tmp_path / "book"
    assert run(capsys, folder, "init")[0] == 0
    assert run(capsys, folder, "account", "add", "Current", "--opening", "100.00")[0] == 0
    code, out, _ = run(capsys, folder, "add", "2026-03-02", "Current", "Corner Shop", "-4.50", "--category",
                       "Groceries")
    assert code == 0
    assert out == "Added #1: 2026-03-02 Corner Shop -4.50\n"
    code, out, _ = run(capsys, folder, "search", "--payee", "corner", "--format", "csv")
    rows = list(csv.reader(io.StringIO(out)))
    assert rows[1] == ["Results", "1", "2026-03-02", "Current", "Corner Shop", "Groceries", "-4.50"]


def test_errors_exit_with_status_1(tmp_path, capsys):
    folder = tmp_path / "book"
    run(capsys, folder, "init")
    code, _, err = run(capsys, folder, "add", "2026-03-02", "Nowhere", "X", "-1.00")
    assert code == 1
    assert err == "error: unknown account: Nowhere\n"
    code, _, err = run(capsys, folder, "add", "2026-03-02", "Nowhere", "X", "lots")
    assert (code, err) == (1, "error: invalid amount: lots\n")


def test_not_a_budget_folder(tmp_path, capsys):
    code, _, err = run(capsys, tmp_path / "missing", "budget", "status", "2026-03")
    assert code == 1
    assert "not a budget folder" in err


def test_import_reports_skipped_rows(tmp_path, capsys):
    folder = tmp_path / "book"
    run(capsys, folder, "init")
    run(capsys, folder, "account", "add", "Current")
    statement = tmp_path / "march.csv"
    statement.write_text("Date,Description,Amount\n2026-03-02,BAKERY,-4.50\n2026-03-03,BAD,x\n", encoding="utf-8")
    code, out, err = run(capsys, folder, "import", "Current", str(statement))
    assert code == 0
    assert out.startswith("Imported 1 transactions into Current (standard layout)")
    assert err == "skipped line 3: invalid amount: x\n"


def test_report_format_comes_from_settings(tmp_path, capsys):
    folder = tmp_path / "book"
    run(capsys, folder, "init")
    run(capsys, folder, "config", "set", "report_format", "csv")
    code, out, _ = run(capsys, folder, "report", "month", "2026-03")
    assert code == 0
    assert out.splitlines()[0] == "section,Item,Amount"
