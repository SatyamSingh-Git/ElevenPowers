import pytest

from ledgerbook import AccountError, Ledger, make_transaction


def test_balances(household):
    assert household.balance("Assets:Bank") == 400000
    assert household.balance("Liabilities:Card") == -4250
    assert household.subtotal("Assets") == 420000
    assert sum(household.balances().values()) == 0


def test_posting_to_an_unopened_account_changes_nothing():
    ledger = Ledger()
    ledger.open("Assets:Cash")
    with pytest.raises(AccountError, match="unknown account: Expenses:Food"):
        ledger.post(make_transaction("2026-03-01", "Lunch", [("Expenses:Food", 1), ("Assets:Cash", -1)]))
    assert ledger.transactions == ()
    assert ledger.balance("Assets:Cash") == 0


def test_postings_for_one_account(household):
    assert [amount for _, amount in household.postings("Assets:Bank")] == [250000, 320000, -150000, -20000]
