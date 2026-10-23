import datetime
import json

from ledgerbook import JournalWriter, Ledger, load_journal, make_transaction, write_journal
from ledgerbook.cli import main


def test_written_journal_keeps_iso_dates_and_loads_dates(tmp_path):
    ledger = Ledger()
    ledger.open("Assets:Cash")
    ledger.open("Equity:Opening")
    ledger.record(datetime.date(2026, 4, 30), "Start", [("Assets:Cash", 700), ("Equity:Opening", -700)])
    path = tmp_path / "books.jsonl"
    write_journal(path, ledger)
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert [r["date"] for r in records if "postings" in r] == ["2026-04-30"]
    again = load_journal(path)
    assert again.transactions[0].date == datetime.date(2026, 4, 30)
    assert again.balances() == ledger.balances()


def test_appending_a_dated_transaction(tmp_path):
    path = tmp_path / "books.jsonl"
    writer = JournalWriter.create(path)
    writer.append_open("Assets:Cash")
    writer.append_open("Equity:Opening")
    writer.append(make_transaction(datetime.date(2026, 5, 1), "Start", [("Assets:Cash", 5), ("Equity:Opening", -5)]))
    assert load_journal(path).transactions[0].date == datetime.date(2026, 5, 1)


def test_command_line_posts_load_as_dates(tmp_path):
    path = str(tmp_path / "books.jsonl")
    assert main([path, "init"]) == 0
    assert main([path, "open", "Assets:Cash", "Equity:Opening"]) == 0
    assert main([path, "post", "2026-05-02", "Start", "Assets:Cash=1", "Equity:Opening"]) == 0
    assert load_journal(path).transactions[0].date == datetime.date(2026, 5, 2)
