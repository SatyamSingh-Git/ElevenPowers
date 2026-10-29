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


def sell(data, when, seats, payment="card"):
    office = office_at(data, when)
    return office.sales.checkout(office.holds.place("HAM-0412E", seats).id, payment=payment)


def daily(capsys, data, *args):
    code, out, err = cli(capsys, data, "2026-04-05T09:00", "report", "daily", "--format", "json", *args)
    assert code == 0, err
    return json.loads(out)


def test_daily_report_has_one_row_per_day(data, capsys):
    first = sell(data, "2026-04-01T10:00", ["A1", "A2"])
    sell(data, "2026-04-02T11:00", ["A3"])
    office_at(data, "2026-04-02T12:00").refunds.refund(first.id, ["A1"])
    assert daily(capsys, data) == [
        {"day": "2026-04-01", "sold": 2, "returned": 0, "sales": 5250, "refunds": 0, "net": 5250},
        {"day": "2026-04-02", "sold": 1, "returned": 1, "sales": 2700, "refunds": 2550, "net": 150},
    ]
    assert [row["day"] for row in daily(capsys, data, "--day", "2026-04-02")] == ["2026-04-02"]


def test_daily_net_after_an_exchange(data, capsys):
    sell(data, "2026-04-02T10:00", ["A8"])
    order = sell(data, "2026-04-03T10:00", ["C1", "C2"])
    settled = office_at(data, "2026-04-03T10:30").refunds.exchange(order.id, "HAM-0413E", ["A1", "A2"])
    [row] = daily(capsys, data, "--day", "2026-04-03")
    assert row["day"] == "2026-04-03"
    assert row["net"] == order.total + settled
    assert sum(row["net"] for row in daily(capsys, data)) == 2550 + 150 + order.total + settled


def test_seat_plan(data, capsys):
    sell(data, "2026-04-01T10:00", ["A1"])
    office_at(data, "2026-04-01T10:00").holds.place("HAM-0412E", ["A2"])
    code, out, err = cli(capsys, data, "2026-04-01T10:05", "seats", "HAM-0412E")
    assert code == 0, err
    rows = {line.split()[0]: line.split()[1:] for line in out.splitlines()
            if line.startswith("  ") and line.split()[0] in ("A", "B", "C")}
    assert rows["A"] == ["1", "x", "h", ".", ".", ".", ".", ".", "."]
    assert rows["B"][:7] == ["1", ".", ".", ".", ".", ".", "."]
    assert rows["C"] == ["1", ".", ".", ".", ".", ".", "."]


def test_cashup_by_payment(data, capsys):
    sell(data, "2026-04-01T10:00", ["A1"], payment="cash")
    sell(data, "2026-04-01T11:00", ["A2", "A3"])
    sell(data, "2026-04-02T11:00", ["A4"], payment="cash")
    code, out, err = cli(capsys, data, "2026-04-05T09:00", "report", "cashup", "--day", "2026-04-01",
                         "--format", "json")
    assert code == 0, err
    rows = {row["payment"]: row for row in json.loads(out)}
    assert (rows["cash"]["entries"], rows["cash"]["amount"]) == (1, 2700)
    assert (rows["card"]["entries"], rows["card"]["amount"]) == (1, 5250)
    assert rows["total"]["amount"] == 7950


def test_occupancy(data, capsys):
    sell(data, "2026-04-01T10:00", ["A1", "A2", "C1"])
    code, out, err = cli(capsys, data, "2026-04-05T09:00", "report", "occupancy", "HAM-0412E", "--format", "json")
    assert code == 0, err
    rows = {row["section"]: row for row in json.loads(out)}
    assert (rows["Stalls"]["sold"], rows["Stalls"]["capacity"]) == (2, 16)
    assert (rows["all"]["sold"], rows["all"]["capacity"]) == (3, 22)
