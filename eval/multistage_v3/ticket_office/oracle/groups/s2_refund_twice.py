import json
from datetime import datetime

import pytest

from boxoffice.cli.main import main
from boxoffice.clock import FixedClock
from boxoffice.errors import BoxOfficeError
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




def ledger_amounts(data):
    return [json.loads(line)["amount"] for line in (data / "ledger.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()]


def test_second_refund_of_a_seat_is_refused(data):
    office = office_at(data, "2026-04-01T10:00")
    order = office.sales.checkout(office.holds.place("HAM-0412E", ["A1", "A2"]).id)
    assert office.refunds.refund(order.id, ["A2"]) == 2550
    with pytest.raises(BoxOfficeError) as raised:
        office_at(data, "2026-04-01T10:30").refunds.refund(order.id, ["A2"])
    assert raised.value.code == "already-refunded"
    assert str(raised.value) == "seat A2 was already refunded"
    assert ledger_amounts(data) == [5250, -2550]


def test_refused_when_named_with_another_seat(data):
    office = office_at(data, "2026-04-01T10:00")
    order = office.sales.checkout(office.holds.place("HAM-0412E", ["A1", "A2"]).id)
    office.refunds.refund(order.id, ["A1"])
    with pytest.raises(BoxOfficeError) as raised:
        office.refunds.refund(order.id, ["A2", "A1"])
    assert raised.value.code == "already-refunded"
    assert str(raised.value) == "seat A1 was already refunded"
    assert office.seat_states("HAM-0412E")["A2"] == "sold"
