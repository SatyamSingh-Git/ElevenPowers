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




def sold(data, seats):
    office = office_at(data, "2026-04-01T10:00")
    return office.sales.checkout(office.holds.place("HAM-0412E", seats).id)


def test_exchange_charges_the_fee(data):
    order = sold(data, ["C1", "C2"])
    settled = office_at(data, "2026-04-02T10:00").refunds.exchange(order.id, "HAM-0413E", ["A1", "A2"])
    assert settled == 2 * 3000 - 2 * 2450 + 100


def test_fee_reduces_what_a_cheaper_exchange_pays_back(data, capsys):
    order = sold(data, ["A1"])
    code, out, err = cli(capsys, data, "2026-04-02T10:00", "exchange", order.id, "--to", "HAM-0413E", "C1")
    assert (code, out.strip()) == (0, f"exchanged order {order.id} to HAM-0413E: settled -4.50")


def test_fee_is_a_setting(data):
    (data / "boxoffice.ini").write_text("[boxoffice]\nexchange_fee = 0\n", encoding="utf-8")
    order = sold(data, ["C1"])
    assert office_at(data, "2026-04-02T10:00").refunds.exchange(order.id, "HAM-0412E", ["C3"]) == 0
    (data / "boxoffice.ini").write_text("[boxoffice]\nexchange_fee = 250\n", encoding="utf-8")
    assert office_at(data, "2026-04-02T10:05").refunds.exchange(order.id, "HAM-0412E", ["C4"]) == 250
