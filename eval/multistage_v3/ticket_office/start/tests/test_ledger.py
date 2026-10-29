from datetime import datetime

from boxoffice.storage.ledger import Ledger


def record(ledger, at, amount):
    return ledger.record_entry("sale", at=at, order="B0001", performance="TEMP-0520",
                               tickets=1, amount=amount, payment="card")


def test_entries_are_appended_in_order(tmp_path):
    ledger = Ledger(tmp_path)
    record(ledger, datetime(2026, 5, 1, 10, 0), 100)
    record(ledger, datetime(2026, 5, 1, 11, 0), 200)
    assert [entry["amount"] for entry in ledger.read_entries()] == [100, 200]


def test_entry_date(tmp_path):
    entry = record(Ledger(tmp_path), datetime(2026, 5, 1, 10, 5), 100)
    assert entry["date"] == "2026-05-01"


def test_entries_on_a_day(tmp_path):
    ledger = Ledger(tmp_path)
    record(ledger, datetime(2026, 5, 1, 23, 59), 100)
    record(ledger, datetime(2026, 5, 2, 0, 0), 200)
    assert [entry["amount"] for entry in ledger.entries_on("2026-05-02")] == [200]


def test_empty_ledger(tmp_path):
    assert Ledger(tmp_path).read_entries() == []
