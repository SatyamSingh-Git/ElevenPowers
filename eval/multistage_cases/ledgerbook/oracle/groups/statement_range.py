from ledgerbook import Ledger, render_statement, statement


def _books():
    ledger = Ledger()
    for name in ("Assets:Bank", "Assets:Cash", "Equity:Opening", "Income:Salary", "Expenses:Rent", "Expenses:Food"):
        ledger.open(name)
    ledger.record("2026-01-01", "Opening deposit", [("Assets:Bank", 500000), ("Equity:Opening", -500000)])
    ledger.record("2026-01-15", "Pay", [("Assets:Bank", 412550), ("Income:Salary", -412550)])
    ledger.record("2026-01-31", "Rent", [("Expenses:Rent", 185000), ("Assets:Bank", -185000)])
    ledger.record("2026-02-01", "Split", [("Assets:Cash", 5), ("Expenses:Food", 1995), ("Assets:Bank", -2000)])
    ledger.record("2026-02-03", "Coffee", [("Expenses:Food", 4), ("Assets:Cash", -4)])
    return ledger


def _rows(lines):
    return [(str(line.date), line.description, line.balance) for line in lines]


def test_range_opens_with_the_carried_balance():
    lines = statement(_books(), "Assets:Bank", start="2026-01-15", end="2026-01-31")
    assert _rows(lines) == [
        ("2026-01-15", "Opening balance", 500000),
        ("2026-01-15", "Pay", 912550),
        ("2026-01-31", "Rent", 727550),
    ]
    assert [line.amount for line in lines[1:]] == [412550, -185000]


def test_end_alone_adds_no_opening_line():
    assert _rows(statement(_books(), "Assets:Bank", end="2026-01-15")) == [
        ("2026-01-01", "Opening deposit", 500000),
        ("2026-01-15", "Pay", 912550),
    ]


def test_start_after_the_last_posting():
    assert _rows(statement(_books(), "Assets:Bank", start="2026-03-01")) == [("2026-03-01", "Opening balance", 725550)]


def test_whole_history_is_unchanged():
    assert [row[1] for row in _rows(statement(_books(), "Assets:Bank"))] == ["Opening deposit", "Pay", "Rent", "Split"]


def test_rendered_range():
    text = render_statement(_books(), "Assets:Cash", start="2026-02-02", end="2026-02-28")
    body = [line.split() for line in text.splitlines()[3:]]
    assert body == [["2026-02-02", "Opening", "balance", "0.05"], ["2026-02-03", "Coffee", "-0.04", "0.01"]]
