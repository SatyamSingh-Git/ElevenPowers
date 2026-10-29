import pytest

from budgetbook.errors import ValidationError
from budgetbook.model.records import RecurringItem
from budgetbook.services import recurring
from budgetbook.storage import journal

from conftest import day


def _rent(**changes):
    fields = dict(name="Rent", account="Current", payee="LANDLORD", amount=-95000, category="Rent",
                  every="month", day=31, start=day("2026-01-01"))
    fields.update(changes)
    return RecurringItem(**fields)


def test_monthly_item_falls_on_the_last_day_of_short_months():
    dates = list(recurring.due_dates(_rent(), day("2026-01-01"), day("2026-04-30")))
    assert [d.isoformat() for d in dates] == ["2026-01-31", "2026-02-28", "2026-03-31", "2026-04-30"]


def test_weekly_item():
    item = _rent(every="week", start=day("2026-03-02"))
    dates = list(recurring.due_dates(item, day("2026-03-01"), day("2026-03-20")))
    assert [d.isoformat() for d in dates] == ["2026-03-02", "2026-03-09", "2026-03-16"]


def test_end_date_stops_an_item():
    dates = list(recurring.due_dates(_rent(end=day("2026-02-15")), day("2026-01-01"), day("2026-06-30")))
    assert len(dates) == 1


def test_post_due_is_idempotent(book):
    recurring.add_item(book, _rent(day=1))
    first = recurring.post_due(book, day("2026-03-15"))
    assert [t.date.isoformat() for t in first] == ["2026-01-01", "2026-02-01", "2026-03-01"]
    assert recurring.post_due(book, day("2026-03-15")) == []
    assert {t.source for t in journal.load_transactions(book.transactions_path)} == {"recurring:Rent"}


def test_upcoming_is_soonest_first(book):
    recurring.add_item(book, _rent(day=1))
    recurring.add_item(book, _rent(name="Gym", amount=-3000, category="Entertainment", every="week",
                                   start=day("2026-03-03")))
    due = recurring.upcoming(book, day("2026-03-01"), day("2026-03-10"))
    assert [(d.isoformat(), item.name) for d, item in due] == [
        ("2026-03-01", "Rent"), ("2026-03-03", "Gym"), ("2026-03-10", "Gym")]


@pytest.mark.parametrize("changes, message", [
    ({"day": 32}, "day must be between 1 and 31"),
    ({"every": "year"}, "every must be one of: month, week"),
    ({"amount": 0}, "amount must not be zero"),
])
def test_add_item_validates(book, changes, message):
    with pytest.raises(ValidationError, match=message):
        recurring.add_item(book, _rent(**changes))
