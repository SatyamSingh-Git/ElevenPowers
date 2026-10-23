from ledgerbook import Ledger, render_trial_balance, statement, summary, trial_balance


def _books():
    ledger = Ledger()
    for name in ("Assets:Bank", "Assets:Cash", "Liabilities:Card", "Equity:Opening",
                 "Income:Salary", "Expenses:Rent", "Expenses:Food"):
        ledger.open(name)
    ledger.record("2026-01-01", "Opening deposit", [("Assets:Bank", 500000), ("Equity:Opening", -500000)])
    ledger.record("2026-01-03", "Groceries", [("Expenses:Food", 8733), ("Liabilities:Card", -8733)])
    ledger.record("2026-01-15", "Pay", [("Assets:Bank", 412550), ("Income:Salary", -412550)])
    ledger.record("2026-01-31", "Rent", [("Expenses:Rent", 185000), ("Assets:Bank", -185000)])
    ledger.record("2026-02-01", "Split", [("Assets:Cash", 5), ("Expenses:Food", 1995), ("Assets:Bank", -2000)])
    return ledger


def test_trial_balance_puts_each_balance_in_its_column():
    report = trial_balance(_books())
    assert {row.account: (row.debit, row.credit) for row in report.rows} == {
        "Assets:Bank": (725550, 0),
        "Assets:Cash": (5, 0),
        "Equity:Opening": (0, 500000),
        "Expenses:Food": (10728, 0),
        "Expenses:Rent": (185000, 0),
        "Income:Salary": (0, 412550),
        "Liabilities:Card": (0, 8733),
    }
    assert report.total_debit == report.total_credit == 921283


def test_overpaid_card_moves_to_the_debit_column():
    ledger = Ledger()
    for name in ("Assets:Bank", "Liabilities:Card", "Equity:Opening"):
        ledger.open(name)
    ledger.record("2026-01-01", "Start", [("Assets:Bank", 10000), ("Equity:Opening", -10000)])
    ledger.record("2026-01-02", "Overpay card", [("Liabilities:Card", 2500), ("Assets:Bank", -2500)])
    rows = {row.account: (row.debit, row.credit) for row in trial_balance(ledger).rows}
    assert rows == {"Assets:Bank": (7500, 0), "Liabilities:Card": (2500, 0), "Equity:Opening": (0, 10000)}


def test_rendered_trial_balance_totals():
    ledger = Ledger()
    for name in ("Assets:Cash", "Liabilities:Card", "Equity:Opening"):
        ledger.open(name)
    ledger.record("2026-01-01", "Start", [("Assets:Cash", 1250), ("Equity:Opening", -1000), ("Liabilities:Card", -250)])
    lines = render_trial_balance(ledger).splitlines()
    assert lines[-1].split() == ["Total", "12.50", "12.50"]
    card = next(line for line in lines if line.startswith("Liabilities:Card"))
    assert card.split() == ["Liabilities:Card", "2.50"]
    assert card.rstrip().endswith("2.50") and len(card.rstrip()) == len(lines[-1].rstrip())


def test_asset_statement_running_balance():
    lines = statement(_books(), "Assets:Bank")
    assert [(str(l.date), l.description, l.amount, l.balance) for l in lines] == [
        ("2026-01-01", "Opening deposit", 500000, 500000),
        ("2026-01-15", "Pay", 412550, 912550),
        ("2026-01-31", "Rent", -185000, 727550),
        ("2026-02-01", "Split", -2000, 725550),
    ]


def test_summary_by_type():
    assert summary(_books()) == {
        "assets": 725555, "liabilities": 8733, "equity": 500000,
        "income": 412550, "expenses": 195728, "net_income": 216822,
    }
