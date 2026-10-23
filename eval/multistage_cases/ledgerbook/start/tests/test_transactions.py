import pytest

from ledgerbook import LedgerError, UnbalancedError, make_transaction, reversal


def test_balanced_transaction():
    txn = make_transaction("2026-03-01", "Lunch", [("Expenses:Food", 1200), ("Assets:Cash", -1200)])
    assert txn.accounts == ("Expenses:Food", "Assets:Cash")
    assert txn.amount_for("Assets:Cash") == -1200


def test_unbalanced():
    with pytest.raises(UnbalancedError, match="off by 100"):
        make_transaction("2026-03-01", "Lunch", [("Expenses:Food", 1300), ("Assets:Cash", -1200)])


@pytest.mark.parametrize("date", ["2026-02-30", "26-03-01", "20260301", None])
def test_bad_dates(date):
    with pytest.raises(LedgerError, match="invalid date"):
        make_transaction(date, "Lunch", [("Expenses:Food", 1), ("Assets:Cash", -1)])


def test_limits():
    with pytest.raises(LedgerError, match="at least 2 postings"):
        make_transaction("2026-03-01", "Lunch", [("Expenses:Food", 0)])
    with pytest.raises(LedgerError, match="more than 16 postings"):
        make_transaction("2026-03-01", "Split", [("Expenses:Food", 1)] * 16 + [("Assets:Cash", -16)])
    with pytest.raises(LedgerError, match="1 to 120 characters"):
        make_transaction("2026-03-01", "x" * 121, [("Expenses:Food", 1), ("Assets:Cash", -1)])


def test_amounts_must_be_integers():
    with pytest.raises(LedgerError, match="must be an integer"):
        make_transaction("2026-03-01", "Lunch", [("Expenses:Food", 12.0), ("Assets:Cash", -12)])


def test_reversal_negates_every_posting():
    txn = make_transaction("2026-03-01", "Lunch", [("Expenses:Food", 1200), ("Assets:Cash", -1200)])
    undo = reversal(txn, "2026-03-02")
    assert undo.description == "Reversal: Lunch"
    assert [p.amount for p in undo.postings] == [-1200, 1200]
