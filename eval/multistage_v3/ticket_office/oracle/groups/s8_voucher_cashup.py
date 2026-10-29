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




def test_counter_sells_for_a_voucher(data, capsys):
    assert cli(capsys, data, "2026-04-01T10:00", "hold", "HAM-0412E", "A1", "A2")[0] == 0
    code, out, err = cli(capsys, data, "2026-04-01T10:01", "sell", "H0001", "--payment", "voucher")
    assert (code, out.strip()) == (0, "order B0001: 2 tickets, total 52.50")


def test_cashup_counts_vouchers_on_their_own(data, capsys):
    office = office_at(data, "2026-04-01T10:00")
    office.sales.checkout(office.holds.place("HAM-0412E", ["A1"]).id, payment="voucher")
    office.sales.checkout(office.holds.place("HAM-0412E", ["A2"]).id, payment="card")
    code, out, err = cli(capsys, data, "2026-04-02T09:00", "report", "cashup", "--day", "2026-04-01",
                         "--format", "json")
    assert code == 0, err
    rows = {row["payment"]: row for row in json.loads(out)}
    assert (rows["voucher"]["entries"], rows["voucher"]["amount"]) == (1, 2700)
    assert (rows["card"]["entries"], rows["card"]["amount"]) == (1, 2700)
    assert rows["total"]["amount"] == 5400
