import pytest

from budgetbook.errors import ValidationError
from budgetbook.model.records import Goal, Rule, Transaction
from budgetbook.services import config, goals, health, renames
from budgetbook.services.accounts import add_account, balances
from budgetbook.services.ledger import add_transaction, categorise_open_months
from budgetbook.services.reconcile import reconcile
from budgetbook.services.transfers import find_pairs
from budgetbook.storage import files, journal

from conftest import day


def test_transfer_pairs_match_the_closest_day():
    transactions = [
        Transaction(1, day("2026-03-01"), "Current", "TO SAVINGS", -10000),
        Transaction(2, day("2026-03-03"), "Savings", "FROM CURRENT", 10000),
        Transaction(3, day("2026-03-02"), "Savings", "FROM CURRENT", 10000),
        Transaction(4, day("2026-03-02"), "Current", "TESCO", -10000, "Groceries"),
    ]
    [pair] = find_pairs(transactions)
    assert (pair.out.id, pair.into.id, pair.days_apart) == (1, 3, 1)


def test_categorise_files_only_open_months(book):
    files.save_rules(book, [Rule("contains", "TESCO", "Groceries")])
    add_transaction(book, day("2026-02-02"), "Current", "TESCO", -1000)
    add_transaction(book, day("2026-03-02"), "Current", "TESCO", -2000)
    book.closed_month_path("2026-02").write_text("{}", encoding="utf-8")
    assert categorise_open_months(book) == 1
    categories = {t.date.month: t.category for t in journal.load_transactions(book.transactions_path)}
    assert categories == {2: "", 3: "Groceries"}


def test_reconcile_points_at_likely_mistakes(book):
    add_transaction(book, day("2026-03-02"), "Current", "TESCO", -2500)
    add_transaction(book, day("2026-03-04"), "Current", "TESCO", -2500)
    result = reconcile(book, "Current", day("2026-03-05"), 97500)
    assert result.difference == 2500
    assert [t.id for t in result.candidates] == [1, 2]
    assert reconcile(book, "Current", day("2026-03-05"), 95000).agrees


def test_goal_progress(book):
    add_account(book, "Savings", "savings", 30000)
    goals.add_goal(book, Goal("Holiday", "Savings", 120000, day("2026-06-30")))
    [progress] = goals.progress(book, day("2026-03-15"))
    assert (progress.saved, progress.still_needed, progress.months_left, progress.per_month) == (
        30000, 90000, 4, 22500)


def test_health_finds_dangling_names(book):
    add_transaction(book, day("2026-03-02"), "Current", "TESCO", -2500)
    files.save_rules(book, [Rule("contains", "X", "Nonsense")])
    assert health.find_problems(book) == ["rule 1 files into unknown category Nonsense"]


def test_rename_account_everywhere(book):
    add_transaction(book, day("2026-03-02"), "Current", "TESCO", -2500)
    files.save_rules(book, [Rule("contains", "TESCO", "Groceries", account="Current")])
    renames.rename_account(book, "Current", "Everyday")
    assert set(files.load_accounts(book)) == {"Everyday"}
    assert journal.load_transactions(book.transactions_path)[0].account == "Everyday"
    assert files.load_rules(book)[0].account == "Everyday"
    assert balances(book) == {"Everyday": 97500}


def test_extra_categories(book):
    config.add_category(book, "Pets", "lifestyle")
    with pytest.raises(ValidationError, match="category already exists: Pets"):
        config.add_category(book, "Pets", "lifestyle")
    renames.rename_category(book, "Pets", "Animals")
    assert book.settings()["extra_categories"] == {"Animals": "lifestyle"}
    with pytest.raises(ValidationError, match="built-in categories cannot be renamed"):
        renames.rename_category(book, "Groceries", "Food")
