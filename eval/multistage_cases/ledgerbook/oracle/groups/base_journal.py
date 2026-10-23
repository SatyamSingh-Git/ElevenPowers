import json

import pytest

from ledgerbook import JournalError, JournalWriter, Ledger, load_journal, make_transaction, write_journal


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


def _shape(ledger):
    return [(str(t.date), t.description, [(p.account, p.amount) for p in t.postings]) for t in ledger.transactions]


def test_write_then_load_gives_the_same_ledger(tmp_path):
    books = _books()
    path = tmp_path / "books.jsonl"
    write_journal(path, books)
    again = load_journal(path)
    assert again.currency == "USD"
    assert again.balances() == books.balances()
    assert _shape(again) == _shape(books)


def test_appended_records_replay(tmp_path):
    path = tmp_path / "books.jsonl"
    writer = JournalWriter.create(path, "EUR")
    writer.append_open("Assets:Bank")
    writer.append_open("Equity:Opening")
    writer.append(make_transaction("2026-01-01", "Start", [("Assets:Bank", 123456), ("Equity:Opening", -123456)]))
    writer.append(make_transaction("2026-01-02", "Fix", [("Assets:Bank", -6), ("Equity:Opening", 6)]))
    ledger = load_journal(path)
    assert ledger.currency == "EUR"
    assert ledger.balance("Assets:Bank") == 123450
    assert len(ledger.transactions) == 2


def _write(tmp_path, records):
    path = tmp_path / "old.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
    return path


V1 = [
    {"ledgerbook": 1, "currency": "USD"},
    {"type": "open", "account": "Assets:Cash"},
    {"type": "open", "account": "Equity:Opening"},
]


def test_hand_written_journal_loads(tmp_path):
    txn = {"type": "txn", "date": "2026-01-01", "description": "Start",
           "postings": [{"account": "Assets:Cash", "amount": 150000}, {"account": "Equity:Opening", "amount": -150000}]}
    ledger = load_journal(_write(tmp_path, V1 + [txn]))
    assert ledger.balance("Assets:Cash") == 150000
    assert str(ledger.transactions[0].date) == "2026-01-01"


def test_bad_line_is_reported_with_its_number(tmp_path):
    txn = {"type": "txn", "date": "2026-01-01", "description": "Start",
           "postings": [{"account": "Assets:Cash", "amount": 1000}, {"account": "Equity:Opening", "amount": -900}]}
    with pytest.raises(JournalError) as info:
        load_journal(_write(tmp_path, V1 + [txn]))
    assert "line 4" in str(info.value) and "does not balance" in str(info.value)
