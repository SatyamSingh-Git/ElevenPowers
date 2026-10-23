import json

from ledgerbook import Ledger, load_journal, write_journal
from ledgerbook.cli import main

V1 = [
    {"ledgerbook": 1, "currency": "USD"},
    {"type": "open", "account": "Assets:Cash"},
    {"type": "open", "account": "Expenses:Food"},
    {"type": "open", "account": "Equity:Opening"},
    {"type": "txn", "date": "2026-01-01", "description": "Start",
     "postings": [{"account": "Assets:Cash", "amount": 250000}, {"account": "Equity:Opening", "amount": -250000}]},
    {"type": "txn", "date": "2026-01-02", "description": "Lunch",
     "postings": [{"account": "Expenses:Food", "amount": 1250}, {"account": "Assets:Cash", "amount": -1250}]},
]


def _old_journal(tmp_path):
    path = tmp_path / "old.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in V1), encoding="utf-8")
    return path


def test_old_whole_number_journal_loads(tmp_path):
    ledger = load_journal(_old_journal(tmp_path))
    assert ledger.balance("Assets:Cash") == 248750
    assert ledger.balance("Expenses:Food") == 1250
    assert len(ledger.transactions) == 2


def test_old_journal_keeps_working_after_new_postings(tmp_path):
    path = _old_journal(tmp_path)
    assert main([str(path), "post", "2026-01-03", "Dinner", "Expenses:Food=20.05", "Assets:Cash"]) == 0
    ledger = load_journal(path)
    assert ledger.balance("Expenses:Food") == 3255
    assert ledger.balance("Assets:Cash") == 246745
    assert len(ledger.transactions) == 3


def test_new_journal_holds_text_and_reads_back(tmp_path):
    ledger = Ledger()
    ledger.open("Assets:Cash")
    ledger.open("Equity:Opening")
    ledger.record("2026-01-01", "Start", [("Assets:Cash", 99), ("Equity:Opening", -99)])
    path = tmp_path / "new.jsonl"
    write_journal(path, ledger)
    last = json.loads(path.read_text(encoding="utf-8").splitlines()[-1])
    assert [p["amount"] for p in last["postings"]] == ["0.99", "-0.99"]
    assert load_journal(path).balance("Assets:Cash") == 99
