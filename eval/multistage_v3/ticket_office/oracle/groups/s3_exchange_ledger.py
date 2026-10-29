import json
from datetime import datetime

import pytest

from boxoffice.cli.main import main
from boxoffice.clock import FixedClock
from boxoffice.services.boxoffice import BoxOffice

SEATMAP = """venue The Playhouse
section Stalls tier=A
row A 1-8
row B 1-8 C:6 W:7,8
section Circle tier=B
row C 1-6
"""


def office_at(data, when):
    return BoxOffice(data, FixedClock(datetime.strptime(when, "%Y-%m-%dT%H:%M")))


def cli(capsys, data, when, *args):
    code = main(["--data", str(data), "--now", when, *args])
    out, err = capsys.readouterr()
    return code, out, err


@pytest.fixture
def data(tmp_path, capsys):
    data = tmp_path / "data"
    seatmap = tmp_path / "playhouse.txt"
    seatmap.write_text(SEATMAP, encoding="utf-8")
    assert cli(capsys, data, "2026-04-01T09:00", "venue", str(seatmap))[0] == 0
    for code, starts, prices in (("HAM-0412E", "2026-04-12T19:30", ["A=25.50", "B=24.50"]),
                                 ("HAM-0413E", "2026-04-13T19:30", ["A=30.00", "B=20.00"])):
        args = ["perf", "add", code, "--title", "Hamlet", "--starts", starts]
        for price in prices:
            args += ["--price", price]
        assert cli(capsys, data, "2026-04-01T09:00", *args)[0] == 0
    return data




def ledger(data):
    return [json.loads(line) for line in (data / "ledger.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()]


def test_exchange_is_one_entry(data):
    office = office_at(data, "2026-04-01T10:00")
    order = office.sales.checkout(office.holds.place("HAM-0412E", ["C1", "C2"]).id, payment="cash")
    settled = office_at(data, "2026-04-02T10:00").refunds.exchange(order.id, "HAM-0413E", ["A1", "A2"])
    entries = ledger(data)
    assert len(entries) == 2
    entry = entries[1]
    assert entry["kind"] == "exchange"
    assert entry["amount"] == settled
    assert entry["order"] == order.id
    assert entry["payment"] == "cash"


def test_exchange_paying_back_is_negative(data):
    office = office_at(data, "2026-04-01T10:00")
    order = office.sales.checkout(office.holds.place("HAM-0412E", ["A1", "A2"]).id)
    settled = office.refunds.exchange(order.id, "HAM-0413E", ["C1", "C2"])
    assert settled == 2 * 2000 - 2 * 2550 + 100
    assert [(entry["kind"], entry["amount"]) for entry in ledger(data)[1:]] == [("exchange", settled)]
