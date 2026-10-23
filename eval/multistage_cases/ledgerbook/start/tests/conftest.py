import pytest

from ledgerbook import Ledger


@pytest.fixture
def household():
    ledger = Ledger()
    for name in ("Assets:Bank", "Assets:Cash", "Liabilities:Card", "Equity:Opening",
                 "Income:Salary", "Expenses:Food", "Expenses:Rent"):
        ledger.open(name)
    ledger.record("2026-01-01", "Opening balance", [("Assets:Bank", 250000), ("Equity:Opening", -250000)])
    ledger.record("2026-01-05", "Groceries", [("Expenses:Food", 4250), ("Liabilities:Card", -4250)])
    ledger.record("2026-01-15", "Salary", [("Assets:Bank", 320000), ("Income:Salary", -320000)])
    ledger.record("2026-01-31", "Rent", [("Expenses:Rent", 150000), ("Assets:Bank", -150000)])
    ledger.record("2026-02-02", "Cash withdrawal", [("Assets:Cash", 20000), ("Assets:Bank", -20000)])
    return ledger
