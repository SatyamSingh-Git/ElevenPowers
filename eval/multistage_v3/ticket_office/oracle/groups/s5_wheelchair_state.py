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




def test_open_wheelchair_spaces_are_reported_as_such(data):
    office = office_at(data, "2026-04-01T10:00")
    states = office.seat_states("HAM-0412E")
    assert (states["B6"], states["B7"], states["B8"]) == ("free", "wheelchair", "wheelchair")
    assert set(states.values()) == {"free", "wheelchair"}


def test_wheelchair_spaces_are_held_sold_and_refunded_by_name(data):
    office = office_at(data, "2026-04-01T10:00")
    hold = office.holds.place("HAM-0412E", ["B7"])
    assert office.seat_states("HAM-0412E")["B7"] == "held"
    order = office.sales.checkout(hold.id)
    assert office.seat_states("HAM-0412E")["B7"] == "sold"
    office.refunds.refund(order.id)
    assert office.seat_states("HAM-0412E")["B7"] == "wheelchair"


def test_exchange_into_a_wheelchair_space(data):
    office = office_at(data, "2026-04-01T10:00")
    order = office.sales.checkout(office.holds.place("HAM-0412E", ["A1"]).id)
    office.refunds.exchange(order.id, "HAM-0413E", ["B8"])
    assert office.seat_states("HAM-0413E")["B8"] == "sold"
    assert office.seat_states("HAM-0412E")["A1"] == "free"
