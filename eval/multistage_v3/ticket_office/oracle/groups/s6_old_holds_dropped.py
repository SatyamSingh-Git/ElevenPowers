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




def checkout_error(data, when, hold_id):
    with pytest.raises(BoxOfficeError) as raised:
        office_at(data, when).sales.checkout(hold_id)
    return raised.value.code


def test_hold_is_dropped_an_hour_after_it_expires(data):
    old = office_at(data, "2026-04-01T10:00").holds.place("HAM-0412E", ["A1"])
    office_at(data, "2026-04-01T11:10").holds.place("HAM-0412E", ["A2"])
    assert checkout_error(data, "2026-04-01T11:11", old.id) == "hold-expired"
    office_at(data, "2026-04-01T11:20").holds.place("HAM-0412E", ["A3"])
    assert checkout_error(data, "2026-04-01T11:21", old.id) == "unknown-hold"


def test_sold_and_released_holds_go_too(data):
    office = office_at(data, "2026-04-01T10:00")
    sold = office.holds.place("HAM-0412E", ["A1"])
    office.sales.checkout(sold.id)
    released = office.holds.place("HAM-0412E", ["A2"])
    office.holds.release(released.id)
    # Still live at 12:00, so whatever numbering is used cannot start again from the first id.
    office_at(data, "2026-04-01T11:50").holds.place("HAM-0412E", ["A4"])
    office_at(data, "2026-04-01T12:00").holds.place("HAM-0412E", ["A3"])
    assert checkout_error(data, "2026-04-01T12:01", sold.id) == "unknown-hold"
    assert checkout_error(data, "2026-04-01T12:01", released.id) == "unknown-hold"
