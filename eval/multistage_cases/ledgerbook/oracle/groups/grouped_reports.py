from ledgerbook import Ledger, render_statement, render_summary, render_trial_balance
from ledgerbook.cli import main


def _books():
    ledger = Ledger()
    for name in ("Assets:Bank", "Liabilities:Card", "Equity:Opening", "Income:Salary", "Expenses:Rent"):
        ledger.open(name)
    ledger.record("2026-01-01", "Opening deposit", [("Assets:Bank", 500000), ("Equity:Opening", -500000)])
    ledger.record("2026-01-15", "Pay", [("Assets:Bank", 412550), ("Income:Salary", -412550)])
    ledger.record("2026-01-31", "Rent", [("Expenses:Rent", 185000), ("Liabilities:Card", -185000)])
    return ledger


def _row(text, label):
    return next(line.split() for line in text.splitlines() if line.startswith(label))


def test_trial_balance_is_grouped():
    text = render_trial_balance(_books())
    assert _row(text, "Assets:Bank") == ["Assets:Bank", "9,125.50"]
    assert _row(text, "Total") == ["Total", "10,975.50", "10,975.50"]


def test_statement_is_grouped():
    text = render_statement(_books(), "Assets:Bank")
    assert text.splitlines()[-1].split() == ["2026-01-15", "Pay", "4,125.50", "9,125.50"]


def test_summary_is_grouped():
    text = render_summary(_books())
    assert _row(text, "Liabilities") == ["Liabilities", "1,850.00"]
    assert _row(text, "Net income") == ["Net", "income", "2,275.50"]


def test_command_line_output_is_grouped(tmp_path, capsys):
    path = str(tmp_path / "books.jsonl")
    assert main([path, "init", "--currency", "JPY"]) == 0
    assert main([path, "open", "Assets:Bank", "Equity:Opening"]) == 0
    assert main([path, "post", "2026-01-01", "Start", "Assets:Bank=2500000", "Equity:Opening"]) == 0
    capsys.readouterr()
    assert main([path, "balances"]) == 0
    assert _row(capsys.readouterr().out, "Total") == ["Total", "2,500,000", "2,500,000"]
