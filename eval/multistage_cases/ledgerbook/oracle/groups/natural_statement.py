from ledgerbook import Ledger, render_statement, statement


def _books():
    ledger = Ledger()
    for name in ("Assets:Bank", "Liabilities:Card", "Equity:Opening", "Income:Salary", "Expenses:Food"):
        ledger.open(name)
    ledger.record("2026-01-01", "Opening deposit", [("Assets:Bank", 50000), ("Equity:Opening", -50000)])
    ledger.record("2026-01-03", "Card purchase", [("Expenses:Food", 4250), ("Liabilities:Card", -4250)])
    ledger.record("2026-01-10", "Card purchase", [("Expenses:Food", 1000), ("Liabilities:Card", -1000)])
    ledger.record("2026-01-15", "Pay", [("Assets:Bank", 41255), ("Income:Salary", -41255)])
    ledger.record("2026-01-20", "Card payment", [("Liabilities:Card", 3000), ("Assets:Bank", -3000)])
    return ledger


def test_liability_statement_runs_positive():
    lines = statement(_books(), "Liabilities:Card")
    assert [(l.amount, l.balance) for l in lines] == [(-4250, 4250), (-1000, 5250), (3000, 2250)]


def test_opening_balance_is_natural_too():
    lines = statement(_books(), "Liabilities:Card", start="2026-01-15")
    assert (lines[0].description, lines[0].balance) == ("Opening balance", 5250)
    assert lines[-1].balance == 2250


def test_income_statement():
    assert [l.balance for l in statement(_books(), "Income:Salary")] == [41255]


def test_asset_statement_is_unchanged():
    assert [l.balance for l in statement(_books(), "Assets:Bank")] == [50000, 91255, 88255]


def test_rendered_card_statement():
    last = render_statement(_books(), "Liabilities:Card").splitlines()[-1].split()
    assert last == ["2026-01-20", "Card", "payment", "30.00", "22.50"]
