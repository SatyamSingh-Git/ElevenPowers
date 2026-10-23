from ledgerbook import Ledger


def _books():
    ledger = Ledger()
    for name in ("Assets:Bank", "Liabilities:Card", "Liabilities:Loan", "Equity:Opening",
                 "Income:Salary", "Expenses:Food", "Expenses:Rent"):
        ledger.open(name)
    ledger.record("2026-01-01", "Opening deposit", [("Assets:Bank", 500000), ("Equity:Opening", -500000)])
    ledger.record("2026-01-03", "Card purchase", [("Expenses:Food", 4250), ("Liabilities:Card", -4250)])
    ledger.record("2026-01-15", "Pay", [("Assets:Bank", 412550), ("Income:Salary", -412550)])
    ledger.record("2026-01-20", "Loan", [("Assets:Bank", 100000), ("Liabilities:Loan", -100000)])
    ledger.record("2026-01-31", "Rent", [("Expenses:Rent", 185000), ("Assets:Bank", -185000)])
    return ledger


def test_credit_normal_accounts_are_positive():
    books = _books()
    assert books.balance("Liabilities:Card") == 4250
    assert books.balance("Equity:Opening") == 500000
    assert books.balance("Income:Salary") == 412550


def test_debit_normal_accounts_are_unchanged():
    books = _books()
    assert books.balance("Assets:Bank") == 827550
    assert books.balance("Expenses:Food") == 4250


def test_balances_and_subtotals():
    books = _books()
    assert books.balances()["Liabilities:Loan"] == 100000
    assert books.balances()["Assets:Bank"] == 827550
    assert books.subtotal("Liabilities") == 104250
    assert books.subtotal("Expenses") == 189250


def test_overpaid_liability_goes_negative():
    books = _books()
    books.record("2026-02-01", "Overpay card", [("Liabilities:Card", 5000), ("Assets:Bank", -5000)])
    assert books.balance("Liabilities:Card") == -750
