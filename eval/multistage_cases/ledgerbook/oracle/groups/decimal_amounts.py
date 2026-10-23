import json

import pytest

from ledgerbook import JournalWriter, Ledger, load_journal, make_transaction, write_journal


def _posted_amounts(path):
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [posting["amount"] for record in records if "postings" in record for posting in record["postings"]]


def _start(currency, minor):
    ledger = Ledger(currency)
    ledger.open("Assets:Cash")
    ledger.open("Equity:Opening")
    ledger.record("2026-01-01", "Start", [("Assets:Cash", minor), ("Equity:Opening", -minor)])
    return ledger


@pytest.mark.parametrize("currency, minor, debit, credit", [
    ("USD", 1250, "12.50", "-12.50"),
    ("USD", -7, "-0.07", "0.07"),
    ("USD", 99999, "999.99", "-999.99"),
    ("JPY", 500, "500", "-500"),
    ("KWD", 1250, "1.250", "-1.250"),
])
def test_written_amounts_are_decimal_text(tmp_path, currency, minor, debit, credit):
    ledger = _start(currency, minor)
    path = tmp_path / "books.jsonl"
    write_journal(path, ledger)
    assert _posted_amounts(path) == [debit, credit]
    assert load_journal(path).balances() == ledger.balances()


@pytest.mark.parametrize("currency, minor", [("USD", 250000), ("USD", -123456789), ("JPY", 1234567), ("KWD", 12345678)])
def test_large_amounts_are_text_and_read_back(tmp_path, currency, minor):
    ledger = _start(currency, minor)
    path = tmp_path / "books.jsonl"
    write_journal(path, ledger)
    assert all(isinstance(amount, str) for amount in _posted_amounts(path))
    assert load_journal(path).balances() == ledger.balances()


def test_appended_amounts_are_decimal_text(tmp_path):
    path = tmp_path / "books.jsonl"
    writer = JournalWriter.create(path, "GBP")
    writer.append_open("Assets:Cash")
    writer.append_open("Equity:Opening")
    writer.append(make_transaction("2026-01-01", "Start", [("Assets:Cash", 30099), ("Equity:Opening", -30099)]))
    writer.append(make_transaction("2026-01-02", "More", [("Assets:Cash", 300000), ("Equity:Opening", -300000)]))
    assert _posted_amounts(path)[:2] == ["300.99", "-300.99"]
    assert load_journal(path).balance("Assets:Cash") == 330099
