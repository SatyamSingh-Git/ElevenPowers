import json

import pytest

from boxoffice.cli.main import main

from conftest import SEATMAP


@pytest.fixture
def run(tmp_path, capsys):
    data = tmp_path / "data"
    seatmap = tmp_path / "hall.txt"
    seatmap.write_text(SEATMAP, encoding="utf-8")

    def run(*args, now="2026-05-01T10:00"):
        code = main(["--data", str(data), "--now", now, *args])
        out, err = capsys.readouterr()
        return code, out.strip(), err.strip()

    run("venue", str(seatmap))
    run("perf", "add", "TEMP-0520", "--title", "The Tempest", "--starts", "2026-05-20T19:30",
        "--price", "A=30", "--price", "B=20.00")
    return run


def test_hold_sell_refund(run):
    assert run("hold", "TEMP-0520", "A1-A2") == (0, "hold H0001: A1 A2 until 2026-05-01T10:15", "")
    assert run("sell", "H0001", "--concession", "A2=child") == (0, "order B0001: 2 tickets, total 46.50", "")
    assert run("refund", "B0001", "A2") == (0, "refunded 15.00 on order B0001", "")


def test_errors_go_to_stderr(run):
    assert run("refund", "B0099") == (1, "", "error: unknown order B0099")


def test_cashup(run):
    run("hold", "TEMP-0520", "C1")
    run("sell", "H0001", "--payment", "cash")
    code, out, _ = run("report", "cashup", "--day", "2026-05-01", "--format", "json")
    assert code == 0
    assert json.loads(out)[1] == {"payment": "cash", "entries": 1, "amount": 2150}


def test_prices(run):
    code, out, _ = run("prices", "TEMP-0520", "--format", "csv")
    assert out.splitlines() == ["tier,adult,child,senior,student", "A,30.00,15.00,24.00,22.50",
                                "B,20.00,10.00,16.00,15.00"]


def test_bad_price(run):
    code, _, err = run("perf", "add", "X-1", "--title", "X", "--starts", "2026-06-01T19:30", "--price", "A=ten")
    assert code == 1
    assert err == "error: --price A=ten: not a price: 'ten'"


def test_check(run):
    assert run("check") == (0, "no problems found", "")
