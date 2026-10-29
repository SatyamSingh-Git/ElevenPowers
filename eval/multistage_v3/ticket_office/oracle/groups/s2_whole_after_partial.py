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




def test_whole_order_refund_pays_only_what_is_left(data):
    office = office_at(data, "2026-04-01T10:00")
    order = office.sales.checkout(office.holds.place("HAM-0412E", ["A1", "A2", "C1"]).id)
    assert office.refunds.refund(order.id, ["A1"]) == 2550
    assert office.refunds.refund(order.id) == 2550 + 2450
    states = office.seat_states("HAM-0412E")
    assert (states["A1"], states["A2"], states["C1"]) == ("free", "free", "free")


def test_counter_reports_the_second_refund(data, capsys):
    assert cli(capsys, data, "2026-04-01T10:00", "hold", "HAM-0412E", "A1", "A2")[0] == 0
    assert cli(capsys, data, "2026-04-01T10:01", "sell", "H0001")[0] == 0
    assert cli(capsys, data, "2026-04-01T10:02", "refund", "B0001", "A1")[0] == 0
    code, out, err = cli(capsys, data, "2026-04-01T10:03", "refund", "B0001", "A1")
    assert (code, err.strip()) == (1, "error: seat A1 was already refunded")
    code, out, err = cli(capsys, data, "2026-04-01T10:04", "refund", "B0001")
    assert (code, out.strip()) == (0, "refunded 25.50 on order B0001")
