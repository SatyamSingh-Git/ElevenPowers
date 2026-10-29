import pytest

from budgetbook.errors import NotFound
from budgetbook.model.records import Rule
from budgetbook.services.accounts import add_account
from budgetbook.services.importing import import_statement
from budgetbook.storage import files, journal

STATEMENT = (
    "Date,Description,Amount\n"
    "2026-03-02,TESCO STORES 3297,-42.50\n"
    "2026-03-02,COSTA COFFEE,-3.25\n"
    "2026-03-02,COSTA COFFEE,-3.25\n"
    "2026-03-03,ACME LTD SALARY,2500.00\n"
)


def test_import_adds_and_files(book):
    files.save_rules(book, [Rule("contains", "TESCO", "Groceries"), Rule("prefix", "ACME", "Salary")])
    result = import_statement(book, "Current", STATEMENT)
    assert result.layout == "standard"
    assert [(t.payee, t.category, t.source) for t in result.added] == [
        ("TESCO STORES 3297", "Groceries", "import:standard"),
        ("COSTA COFFEE", "", "import:standard"),
        ("COSTA COFFEE", "", "import:standard"),
        ("ACME LTD SALARY", "Salary", "import:standard"),
    ]


def test_reimport_skips_what_is_there(book):
    import_statement(book, "Current", STATEMENT)
    overlapping = STATEMENT + "2026-03-04,COSTA COFFEE,-3.25\n"
    result = import_statement(book, "Current", overlapping)
    assert result.duplicates == 4
    assert [t.date.isoformat() for t in result.added] == ["2026-03-04"]
    assert len(journal.load_transactions(book.transactions_path)) == 5


def test_same_rows_in_another_account_are_not_duplicates(book):
    add_account(book, "Joint")
    import_statement(book, "Current", STATEMENT)
    assert len(import_statement(book, "Joint", STATEMENT).added) == 4


def test_rows_in_closed_months_are_left_out(book):
    book.closed_month_path("2026-03").write_text("{}", encoding="utf-8")
    result = import_statement(book, "Current", STATEMENT)
    assert result.added == []
    assert [str(p) for p in result.problems][0] == "line 2: month is closed: 2026-03"


def test_dry_run_stores_nothing(book):
    result = import_statement(book, "Current", STATEMENT, dry_run=True)
    assert len(result.added) == 4
    assert journal.load_transactions(book.transactions_path) == []


def test_unknown_account(book):
    with pytest.raises(NotFound, match="unknown account: Savings"):
        import_statement(book, "Savings", STATEMENT)
