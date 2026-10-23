import datetime

import pytest

from ledgerbook import Ledger, LedgerError, make_transaction, statement

PAIR = [("Expenses:Food", 1200), ("Assets:Cash", -1200)]


def test_text_dates_become_dates():
    assert make_transaction("2026-03-01", "Lunch", PAIR).date == datetime.date(2026, 3, 1)


def test_date_objects_are_accepted():
    txn = make_transaction(datetime.date(2026, 3, 1), "Lunch", PAIR)
    assert txn.date == datetime.date(2026, 3, 1)
    assert txn == make_transaction("2026-03-01", "Lunch", PAIR)


def test_ledger_record_takes_either():
    ledger = Ledger()
    ledger.open("Assets:Cash")
    ledger.open("Expenses:Food")
    ledger.record(datetime.date(2026, 3, 1), "Lunch", PAIR)
    ledger.record("2026-03-02", "Lunch", PAIR)
    assert [t.date for t in ledger.transactions] == [datetime.date(2026, 3, 1), datetime.date(2026, 3, 2)]
    assert (ledger.transactions[1].date - ledger.transactions[0].date).days == 1


@pytest.mark.parametrize("value", ["2026-02-30", "01/03/2026", "2026-3-1", None, 20260301])
def test_other_values_are_refused(value):
    with pytest.raises(LedgerError, match="invalid date"):
        make_transaction(value, "Lunch", PAIR)


def test_statement_dates_and_bounds():
    ledger = Ledger()
    for name in ("Assets:Cash", "Expenses:Food", "Equity:Opening"):
        ledger.open(name)
    ledger.record("2026-03-01", "Float", [("Assets:Cash", 10000), ("Equity:Opening", -10000)])
    ledger.record("2026-03-05", "Lunch", PAIR)
    ledger.record("2026-03-09", "Lunch", PAIR)
    lines = statement(ledger, "Assets:Cash", start=datetime.date(2026, 3, 2), end=datetime.date(2026, 3, 5))
    assert [(l.date, l.balance) for l in lines] == [(datetime.date(2026, 3, 2), 10000), (datetime.date(2026, 3, 5), 8800)]
    mixed = statement(ledger, "Assets:Cash", start="2026-03-02", end=datetime.date(2026, 3, 9))
    assert [l.date for l in mixed] == [datetime.date(2026, 3, 2), datetime.date(2026, 3, 5), datetime.date(2026, 3, 9)]
