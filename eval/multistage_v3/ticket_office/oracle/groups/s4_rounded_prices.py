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




def prices(data, seats, concessions):
    office = office_at(data, "2026-04-01T10:00")
    order = office.sales.checkout(office.holds.place("HAM-0412E", seats).id, dict(zip(seats, concessions)))
    return {line.seat: line.price for line in order.lines}


def test_concessions_round_to_fifty_pence(data):
    names = ["adult", "child", "senior", "student"]
    assert prices(data, ["A1", "A2", "A3", "A4"], names) == {"A1": 2550, "A2": 1300, "A3": 2050, "A4": 1900}
    assert prices(data, ["C1", "C2", "C3", "C4"], names) == {"C1": 2450, "C2": 1250, "C3": 1950, "C4": 1850}


def test_order_total_uses_the_rounded_prices(data):
    office = office_at(data, "2026-04-01T10:00")
    order = office.sales.checkout(office.holds.place("HAM-0412E", ["A5", "A6"]).id, {"A6": "child"})
    assert order.total == 2550 + 1300 + 150
