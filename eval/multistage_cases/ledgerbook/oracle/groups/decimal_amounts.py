import json

import pytest

from ledgerbook import JournalWriter, Ledger, load_journal, make_transaction, write_journal


def _posted_amounts(path):
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [posting["amount"] for record in records if "postings" in record for posting in record["postings"]]


@pytest.mark.parametrize("currency, minor, debit, credit", [
    ("USD", 1250, "12.50", "-12.50"),
    ("USD", -7, "-0.07", "0.07"),
    ("USD", 250000, "2500.00", "-2500.00"),
    ("USD", 123456789, "1234567.89", "-1234567.89"),
    ("JPY", 500, "500", "-500"),
    ("JPY", 1234567, "1234567", "-1234567"),
    ("KWD", 1250, "1.250", "-1.250"),
])
def test_written_amounts_are_decimal_text(tmp_path, currency, minor, debit, credit):
    ledger = Ledger(currency)
    ledger.open("Assets:Cash")
    ledger.open("Equity:Opening")
    ledger.record("2026-01-01", "Start", [("Assets:Cash", minor), ("Equity:Opening", -minor)])
    path = tmp_path / "books.jsonl"
    write_journal(path, ledger)
    assert _posted_amounts(path) == [debit, credit]
    assert load_journal(path).balances() == ledger.balances()


def test_appended_amounts_are_decimal_text(tmp_path):
    path = tmp_path / "books.jsonl"
    writer = JournalWriter.create(path, "GBP")
    writer.append_open("Assets:Cash")
    writer.append_open("Equity:Opening")
    writer.append(make_transaction("2026-01-01", "Start", [("Assets:Cash", 300099), ("Equity:Opening", -300099)]))
    assert _posted_amounts(path) == ["3000.99", "-3000.99"]
    assert load_journal(path).balance("Assets:Cash") == 300099
