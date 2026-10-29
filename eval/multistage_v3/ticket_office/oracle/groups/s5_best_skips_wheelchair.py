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




def test_best_available_never_picks_a_wheelchair_space(data):
    office = office_at(data, "2026-04-01T10:00")
    office.sales.checkout(office.holds.place("HAM-0412E", [f"A{n}" for n in range(1, 9)]).id)
    with pytest.raises(BoxOfficeError) as raised:
        office.holds.place_best("HAM-0412E", 7, section="Stalls")
    assert raised.value.code == "not-enough-seats"
    assert office.holds.place_best("HAM-0412E", 6, section="Stalls").seats == ["B1", "B2", "B3", "B4", "B5", "B6"]
    assert office.holds.place_best("HAM-0412E", 2).seats == ["C1", "C2"]


def test_counter_best_available_skips_them(data, capsys):
    office = office_at(data, "2026-04-01T10:00")
    office.sales.checkout(office.holds.place("HAM-0412E", [f"A{n}" for n in range(1, 9)]).id)
    office.sales.checkout(office.holds.place("HAM-0412E", ["B1", "B2", "B3", "B4", "B5"]).id)
    code, out, err = cli(capsys, data, "2026-04-01T10:05", "hold", "HAM-0412E", "--best", "2", "--section", "Stalls")
    assert (code, err.strip()) == (1, "error: no block of 2 seats available")
    code, out, err = cli(capsys, data, "2026-04-01T10:05", "hold", "HAM-0412E", "B7", "B8")
    assert code == 0, err
