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




def test_price_list_shows_rounded_concessions(data, capsys):
    code, out, err = cli(capsys, data, "2026-04-01T10:00", "prices", "HAM-0412E", "--format", "json")
    assert code == 0, err
    rows = {row["tier"]: row for row in json.loads(out)}
    assert rows["A"] == {"tier": "A", "adult": 2550, "child": 1300, "senior": 2050, "student": 1900}
    assert rows["B"] == {"tier": "B", "adult": 2450, "child": 1250, "senior": 1950, "student": 1850}


def test_refund_pays_back_the_rounded_price(data):
    office = office_at(data, "2026-04-01T10:00")
    order = office.sales.checkout(office.holds.place("HAM-0412E", ["C1", "C2"]).id, {"C2": "child"})
    assert office.refunds.refund(order.id, ["C2"]) == 1250


def test_exchange_reprices_with_rounding(data):
    office = office_at(data, "2026-04-01T10:00")
    order = office.sales.checkout(office.holds.place("HAM-0413E", ["C1"]).id, {"C1": "student"})
    assert order.total == 1500 + 150
    office.refunds.exchange(order.id, "HAM-0412E", ["A1"])
    assert [line.price for line in office.order(order.id).lines] == [1900]
