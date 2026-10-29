import json

import pytest

from budgetbook.errors import ValidationError
from budgetbook.model.dates import Month
from budgetbook.services import budgets, closing
from budgetbook.services.ledger import add_transaction

from conftest import day


def _march(book):
    budgets.set_budget(book, "Groceries", 40000, rollover=True)
    add_transaction(book, day("2026-03-01"), "Current", "ACME LTD", 250000, "Salary")
    add_transaction(book, day("2026-03-02"), "Current", "TESCO", -12050, "Groceries")
    add_transaction(book, day("2026-03-03"), "Current", "CINEMA", -2400, "Entertainment")


def test_close_writes_the_month_file(book):
    _march(book)
    closing.close_month(book, Month(2026, 3))
    data = json.loads(book.closed_month_path("2026-03").read_text(encoding="utf-8"))
    assert data == {
        "format": 1,
        "month": "2026-03",
        "currency": "GBP",
        "income": 250000,
        "spending": 14450,
        "categories": [
            {"name": "Groceries", "group": "essentials", "budget": 40000, "carried": 0, "spent": 12050,
             "remaining": 27950},
        ],
    }


def test_closed_month_is_locked(book):
    _march(book)
    closing.close_month(book, Month(2026, 3))
    with pytest.raises(ValidationError, match="month is closed: 2026-03"):
        add_transaction(book, day("2026-03-30"), "Current", "TESCO", -100, "Groceries")
    with pytest.raises(ValidationError, match="month already closed: 2026-03"):
        closing.close_month(book, Month(2026, 3))


def test_reopen(book):
    _march(book)
    closing.close_month(book, Month(2026, 3))
    closing.reopen_month(book, Month(2026, 3))
    assert not book.is_closed(Month(2026, 3))
    with pytest.raises(ValidationError, match="month is not closed"):
        closing.reopen_month(book, Month(2026, 3))
