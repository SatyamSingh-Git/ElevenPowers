import pytest

from ledgerbook import load_journal
from ledgerbook.cli import main


@pytest.fixture
def books(tmp_path):
    path = str(tmp_path / "books.jsonl")
    assert main([path, "init"]) == 0
    assert main([path, "open", "Assets:Cash", "Expenses:Food", "Equity:Opening"]) == 0
    assert main([path, "post", "2026-01-01", "Start", "Assets:Cash=100", "Equity:Opening"]) == 0
    return path


def test_post_and_balances(books, capsys):
    assert main([books, "post", "2026-01-02", "Lunch", "Expenses:Food=12.50", "Assets:Cash=-12.50"]) == 0
    capsys.readouterr()
    assert main([books, "balances"]) == 0
    out = capsys.readouterr().out
    assert "Assets:Cash" in out and "87.50" in out
    assert load_journal(books).balance("Expenses:Food") == 1250


def test_errors_exit_one_and_write_nothing(books, capsys):
    before = open(books, encoding="utf-8").read()
    assert main([books, "post", "2026-01-02", "Lunch", "Expenses:Food=12.50", "Assets:Cash=-12"]) == 1
    assert capsys.readouterr().err == "error: transaction does not balance: off by 50\n"
    assert main([books, "open", "Assets:Bank", "Assets:Cash"]) == 1
    assert open(books, encoding="utf-8").read() == before


def test_reverse(books, capsys):
    assert main([books, "reverse", "1", "2026-01-03"]) == 0
    assert load_journal(books).balance("Assets:Cash") == 0
    assert main([books, "reverse", "5", "2026-01-03"]) == 1
    assert "no transaction number 5" in capsys.readouterr().err


def test_statement_and_summary(books, capsys):
    assert main([books, "statement", "Assets:Cash"]) == 0
    assert "Start" in capsys.readouterr().out
    assert main([books, "summary"]) == 0
    assert "Equity" in capsys.readouterr().out
