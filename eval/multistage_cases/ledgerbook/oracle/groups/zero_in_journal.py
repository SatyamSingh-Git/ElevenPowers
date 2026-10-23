import json

import pytest

from ledgerbook import JournalError, load_journal

RECORDS = [
    {"ledgerbook": 1, "currency": "USD"},
    {"type": "open", "account": "Assets:Cash"},
    {"type": "open", "account": "Expenses:Food"},
    {"type": "txn", "date": "2026-03-01", "description": "Lunch",
     "postings": [{"account": "Expenses:Food", "amount": 900}, {"account": "Assets:Cash", "amount": -900}]},
    {"type": "txn", "date": "2026-03-02", "description": "Oops",
     "postings": [{"account": "Expenses:Food", "amount": 0}, {"account": "Assets:Cash", "amount": 0}]},
]


def test_journal_with_a_zero_posting_fails_at_its_line(tmp_path):
    path = tmp_path / "books.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in RECORDS), encoding="utf-8")
    with pytest.raises(JournalError) as info:
        load_journal(path)
    assert "line 5" in str(info.value)
    assert "posting amount must not be zero: Expenses:Food" in str(info.value)


def test_journal_without_it_still_loads(tmp_path):
    path = tmp_path / "books.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in RECORDS[:-1]), encoding="utf-8")
    assert load_journal(path).balance("Expenses:Food") == 900
