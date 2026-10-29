import pytest

from budgetbook.errors import BudgetError
from budgetbook.model.records import Transaction
from budgetbook.storage import journal

from conftest import day


def _txn(date, payee, amount, **extra):
    return Transaction(0, day(date), "Current", payee, amount, **extra)


def test_round_trip(tmp_path):
    path = tmp_path / "transactions.csv"
    stored = journal.append_transactions(path, [
        _txn("2026-03-02", "BAKERY", -450, category="Groceries", memo="bread, rolls"),
        _txn("2026-03-01", "ACME LTD", 250000, category="Salary", source="import:standard"),
    ])
    assert [t.id for t in stored] == [1, 2]
    loaded = journal.load_transactions(path)
    assert {t.id: t for t in loaded} == {t.id: t for t in stored}


def test_ids_continue_from_the_highest(tmp_path):
    path = tmp_path / "transactions.csv"
    journal.append_transactions(path, [_txn("2026-03-01", "A", -100), _txn("2026-03-02", "B", -200)])
    added = journal.append_transactions(path, [_txn("2026-02-01", "C", -300)])
    assert added[0].id == 3


def test_file_is_sorted_by_date(tmp_path):
    path = tmp_path / "transactions.csv"
    journal.append_transactions(path, [_txn("2026-03-05", "LATER", -100)])
    journal.append_transactions(path, [_txn("2026-03-01", "EARLIER", -100)])
    assert [t.payee for t in journal.load_transactions(path)] == ["EARLIER", "LATER"]


def test_header_is_checked(tmp_path):
    path = tmp_path / "transactions.csv"
    path.write_text("date,amount\n2026-03-01,1.00\n", encoding="utf-8")
    with pytest.raises(BudgetError, match="unexpected header"):
        journal.load_transactions(path)


def test_bad_line_names_its_number(tmp_path):
    path = tmp_path / "transactions.csv"
    path.write_text(",".join(journal.COLUMNS) + "\n1,2026-03-01,Current,X,lots,,,manual\n", encoding="utf-8")
    with pytest.raises(BudgetError, match="line 2"):
        journal.load_transactions(path)


def test_missing_file_is_empty(tmp_path):
    assert journal.load_transactions(tmp_path / "nothing.csv") == []
