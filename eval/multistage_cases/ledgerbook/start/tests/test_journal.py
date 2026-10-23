import json

import pytest

from ledgerbook import JournalError, JournalWriter, LedgerError, load_journal, make_transaction, write_journal


def test_round_trip(household, tmp_path):
    path = tmp_path / "books.jsonl"
    write_journal(path, household)
    again = load_journal(path)
    assert again.balances() == household.balances()
    assert again.transactions == household.transactions


def test_file_layout(household, tmp_path):
    path = tmp_path / "books.jsonl"
    write_journal(path, household)
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert records[0] == {"ledgerbook": 1, "currency": "USD"}
    assert records[1] == {"type": "open", "account": "Assets:Bank"}
    assert records[-1]["postings"] == [{"account": "Assets:Cash", "amount": 20000},
                                       {"account": "Assets:Bank", "amount": -20000}]


def test_writer_appends(tmp_path):
    path = tmp_path / "books.jsonl"
    writer = JournalWriter.create(path, "EUR")
    writer.append_open("Assets:Cash")
    writer.append_open("Equity:Opening")
    writer.append(make_transaction("2026-01-01", "Start", [("Assets:Cash", 500), ("Equity:Opening", -500)]))
    ledger = load_journal(path)
    assert ledger.currency == "EUR"
    assert ledger.balance("Assets:Cash") == 500
    with pytest.raises(LedgerError, match="journal already exists"):
        JournalWriter.create(path)


def _journal(tmp_path, *records):
    path = tmp_path / "books.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
    return path


HEADER = {"ledgerbook": 1, "currency": "USD"}
OPEN_CASH = {"type": "open", "account": "Assets:Cash"}


def test_errors_carry_the_line(tmp_path):
    bad = {"type": "txn", "date": "2026-01-01", "description": "x",
           "postings": [{"account": "Assets:Cash", "amount": 5}, {"account": "Assets:Cash", "amount": -4}]}
    with pytest.raises(JournalError, match="line 3: transaction does not balance: off by 1"):
        load_journal(_journal(tmp_path, HEADER, OPEN_CASH, bad))
    with pytest.raises(JournalError, match="line 2: unknown record type: close"):
        load_journal(_journal(tmp_path, HEADER, {"type": "close"}))
    with pytest.raises(JournalError, match="line 1: unsupported journal version: 9"):
        load_journal(_journal(tmp_path, {"ledgerbook": 9, "currency": "USD"}))


def test_empty_and_garbled(tmp_path):
    path = tmp_path / "books.jsonl"
    path.write_text("", encoding="utf-8")
    with pytest.raises(JournalError, match="line 1: missing header"):
        load_journal(path)
    path.write_text(json.dumps(HEADER) + "\n{oops\n", encoding="utf-8")
    with pytest.raises(JournalError, match="line 2: not valid JSON"):
        load_journal(path)
