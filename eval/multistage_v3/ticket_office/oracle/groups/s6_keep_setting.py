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


def test_keep_time_is_a_setting(data):
    (data / "boxoffice.ini").write_text("[boxoffice]\nhold_keep_minutes = 5\n", encoding="utf-8")
    old = office_at(data, "2026-04-01T10:00").holds.place("HAM-0412E", ["A1"])
    office_at(data, "2026-04-01T10:19").holds.place("HAM-0412E", ["A2"])
    assert checkout_error(data, "2026-04-01T10:19", old.id) == "hold-expired"
    office_at(data, "2026-04-01T10:21").holds.place("HAM-0412E", ["A3"])
    assert checkout_error(data, "2026-04-01T10:21", old.id) == "unknown-hold"


def test_default_keeps_an_expired_hold_for_an_hour(data):
    old = office_at(data, "2026-04-01T10:00").holds.place("HAM-0412E", ["A1"])
    office_at(data, "2026-04-01T11:15").holds.place("HAM-0412E", ["A2"])
    assert checkout_error(data, "2026-04-01T11:15", old.id) == "hold-expired"
    office_at(data, "2026-04-01T11:16").holds.place("HAM-0412E", ["A3"])
    assert checkout_error(data, "2026-04-01T11:16", old.id) == "unknown-hold"
