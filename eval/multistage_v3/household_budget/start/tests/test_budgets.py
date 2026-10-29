import json

import pytest

from budgetbook.errors import ValidationError
from budgetbook.model.dates import Month
from budgetbook.services import budgets
from budgetbook.services.ledger import add_transaction

from conftest import day


def _status(book, month):
    return {line.category: line for line in budgets.budget_status(book, Month.parse(month))}


def test_status_counts_spending_in_the_month(book):
    budgets.set_budget(book, "Groceries", 40000)
    add_transaction(book, day("2026-03-02"), "Current", "TESCO", -12050, "Groceries")
    add_transaction(book, day("2026-03-20"), "Current", "ASDA", -5000, "Groceries")
    add_transaction(book, day("2026-04-01"), "Current", "TESCO", -9900, "Groceries")
    line = _status(book, "2026-03")["Groceries"]
    assert (line.budget, line.carried, line.spent, line.remaining) == (40000, 0, 17050, 22950)


def test_refunds_do_not_count(book):
    budgets.set_budget(book, "Clothing", 10000)
    add_transaction(book, day("2026-03-02"), "Current", "ZARA", -8000, "Clothing")
    add_transaction(book, day("2026-03-09"), "Current", "ZARA", 3000, "Clothing")
    assert _status(book, "2026-03")["Clothing"].spent == 8000


def test_rollover_carries_what_was_left(book):
    budgets.set_budget(book, "Groceries", 40000, rollover=True)
    budgets.set_budget(book, "Clothing", 10000)
    book.closed_month_path("2026-02").write_text(json.dumps({
        "format": 1, "month": "2026-02", "currency": "GBP", "income": 0, "spending": 0,
        "categories": [
            {"name": "Groceries", "group": "essentials", "budget": 40000, "carried": 0, "spent": 35000,
             "remaining": 5000},
            {"name": "Clothing", "group": "lifestyle", "budget": 10000, "carried": 0, "spent": 0,
             "remaining": 10000},
        ],
    }), encoding="utf-8")
    status = _status(book, "2026-03")
    assert status["Groceries"].carried == 5000
    assert status["Groceries"].available == 45000
    assert status["Clothing"].carried == 0


def test_negative_budget_is_refused(book):
    with pytest.raises(ValidationError, match="budget must not be negative: -5.00"):
        budgets.set_budget(book, "Groceries", -500)


def test_suggest_rounds_averages_up(book):
    add_transaction(book, day("2026-01-10"), "Current", "TESCO", -30000, "Groceries")
    add_transaction(book, day("2026-02-10"), "Current", "TESCO", -32050, "Groceries")
    add_transaction(book, day("2026-03-10"), "Current", "TESCO", -31000, "Groceries")
    assert budgets.suggest(book, Month(2026, 4)) == {"Groceries": 31100}
