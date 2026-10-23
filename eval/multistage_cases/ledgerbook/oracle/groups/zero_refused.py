import pytest

from ledgerbook import Ledger, LedgerError, make_transaction
from ledgerbook.cli import main


def test_zero_posting_is_refused():
    with pytest.raises(LedgerError) as info:
        make_transaction("2026-03-01", "Oops", [("Expenses:Food", 0), ("Assets:Cash", 0)])
    assert str(info.value) == "posting amount must not be zero: Expenses:Food"


def test_first_zero_posting_is_named():
    with pytest.raises(LedgerError) as info:
        make_transaction("2026-03-01", "Oops", [("Expenses:Food", 500), ("Assets:Bank", 0), ("Assets:Cash", -500)])
    assert str(info.value) == "posting amount must not be zero: Assets:Bank"


def test_ledger_is_unchanged():
    ledger = Ledger()
    ledger.open("Assets:Cash")
    ledger.open("Expenses:Food")
    with pytest.raises(LedgerError):
        ledger.record("2026-03-01", "Oops", [("Expenses:Food", 0), ("Assets:Cash", 0)])
    assert ledger.transactions == ()


def test_command_line_refuses_and_writes_nothing(tmp_path, capsys):
    path = tmp_path / "books.jsonl"
    assert main([str(path), "init"]) == 0
    assert main([str(path), "open", "Assets:Cash", "Expenses:Food"]) == 0
    before = path.read_bytes()
    assert main([str(path), "post", "2026-03-01", "Oops", "Expenses:Food=0", "Assets:Cash=0"]) == 1
    assert "posting amount must not be zero: Expenses:Food" in capsys.readouterr().err
    assert path.read_bytes() == before
