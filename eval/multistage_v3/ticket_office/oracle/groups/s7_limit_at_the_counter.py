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




def test_counter_holds_eleven(data, capsys):
    code, out, err = cli(capsys, data, "2026-04-01T10:00", "hold", "HAM-0412E", "A1-A8", "C1-C3")
    assert code == 0, err
    assert out.strip().startswith("hold H0001: A1 A2 A3 A4 A5 A6 A7 A8 C1 C2 C3 until")


def test_venue_limit_still_wins(data, capsys):
    (data / "boxoffice.ini").write_text("[boxoffice]\nmax_tickets_per_order = 4\n", encoding="utf-8")
    code, out, err = cli(capsys, data, "2026-04-01T10:00", "hold", "HAM-0412E", "A1-A5")
    assert (code, err.strip()) == (1, "error: at most 4 tickets per order")
    code, out, err = cli(capsys, data, "2026-04-01T10:00", "hold", "HAM-0412E", "--best", "12")
    assert (code, err.strip()) == (1, "error: at most 4 tickets per order")
