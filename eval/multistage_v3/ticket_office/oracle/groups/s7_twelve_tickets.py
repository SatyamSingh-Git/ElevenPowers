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




def test_twelve_seats_fit_in_one_order(data):
    office = office_at(data, "2026-04-01T10:00")
    seats = [f"A{n}" for n in range(1, 9)] + ["C1", "C2", "C3", "C4"]
    order = office.sales.checkout(office.holds.place("HAM-0412E", seats).id)
    assert len(order.lines) == 12


def test_thirteen_do_not(data):
    office = office_at(data, "2026-04-01T10:00")
    seats = [f"A{n}" for n in range(1, 9)] + ["C1", "C2", "C3", "C4", "C5"]
    with pytest.raises(BoxOfficeError) as raised:
        office.holds.place("HAM-0412E", seats)
    assert raised.value.code == "too-many"
    assert str(raised.value) == "at most 12 tickets per order"
