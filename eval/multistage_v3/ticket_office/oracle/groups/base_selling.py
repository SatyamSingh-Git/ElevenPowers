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


def test_holds_placed_after_earlier_ones_lapse_keep_their_own_seats(data):
    first = office_at(data, "2026-04-01T10:00").holds.place("HAM-0412E", ["A1"])
    second = office_at(data, "2026-04-01T11:12").holds.place("HAM-0412E", ["A2"])
    third = office_at(data, "2026-04-01T11:20").holds.place("HAM-0412E", ["A3"])
    fourth = office_at(data, "2026-04-01T11:22").holds.place("HAM-0412E", ["A4"])
    assert len({second.id, third.id, fourth.id}) == 3
    assert first.id != second.id
    later = office_at(data, "2026-04-01T11:23")
    assert later.seat_states("HAM-0412E")["A1"] == "free"
    for hold, seat in ((second, "A2"), (third, "A3"), (fourth, "A4")):
        assert [line.seat for line in later.sales.checkout(hold.id).lines] == [seat]
    states = later.seat_states("HAM-0412E")
    assert (states["A2"], states["A3"], states["A4"]) == ("sold", "sold", "sold")


def test_hold_expires_after_hold_minutes(data):
    hold = office_at(data, "2026-04-01T10:00").holds.place("HAM-0412E", ["C3", "C1"])
    assert hold.seats == ["C1", "C3"]
    with pytest.raises(BoxOfficeError) as raised:
        office_at(data, "2026-04-01T10:15").sales.checkout(hold.id)
    assert raised.value.code == "hold-expired"


def test_price_list_shows_what_checkout_charges(data, capsys):
    code, out, _ = cli(capsys, data, "2026-04-01T10:00", "prices", "HAM-0412E", "--format", "json")
    assert code == 0
    listed = {row["tier"]: row for row in json.loads(out)}
    office = office_at(data, "2026-04-01T10:00")
    names = ["adult", "child", "senior", "student"]
    for tier, seats in (("A", ["A1", "A2", "A3", "A4"]), ("B", ["C1", "C2", "C3", "C4"])):
        hold = office.holds.place("HAM-0412E", seats)
        order = office.sales.checkout(hold.id, dict(zip(seats, names)))
        assert sorted(line.concession for line in order.lines) == sorted(names)
        for line in order.lines:
            assert listed[tier][line.concession] == line.price
    assert listed["A"]["adult"] == 2550


def test_checkout_charges_the_booking_fee_once(data):
    office = office_at(data, "2026-04-01T10:00")
    order = office.sales.checkout(office.holds.place("HAM-0412E", ["A5", "A6"]).id)
    assert order.total == 2550 * 2 + 150


def test_refunds(data):
    office = office_at(data, "2026-04-01T10:00")
    order = office.sales.checkout(office.holds.place("HAM-0412E", ["A1", "A2"]).id, {"A2": "child"})
    child = next(line.price for line in order.lines if line.seat == "A2")
    assert office.refunds.refund(order.id, ["A2"]) == child
    assert office.seat_states("HAM-0412E")["A2"] == "free"
    other = office.sales.checkout(office.holds.place("HAM-0412E", ["A3", "A4"]).id)
    assert office.refunds.refund(other.id) == 2550 * 2
    late = office_at(data, "2026-04-10T19:31")
    third = office.sales.checkout(office.holds.place("HAM-0412E", ["A5"]).id)
    with pytest.raises(BoxOfficeError) as raised:
        late.refunds.refund(third.id)
    assert raised.value.code == "refund-closed"


def test_exchange_moves_the_seats(data):
    office = office_at(data, "2026-04-01T10:00")
    order = office.sales.checkout(office.holds.place("HAM-0412E", ["C1", "C2"]).id)
    amount = office.refunds.exchange(order.id, "HAM-0413E", ["A1", "A2"])
    assert isinstance(amount, int)
    assert office.seat_states("HAM-0412E")["C1"] == "free"
    assert office.seat_states("HAM-0413E")["A1"] == "sold"


def test_cli_hold_and_sell(data, capsys):
    code, out, _ = cli(capsys, data, "2026-04-01T10:00", "hold", "HAM-0412E", "A1", "A2")
    assert (code, out.strip()) == (0, "hold H0001: A1 A2 until 2026-04-01T10:15")
    code, out, _ = cli(capsys, data, "2026-04-01T10:05", "sell", "H0001", "--payment", "cash")
    assert (code, out.strip()) == (0, "order B0001: 2 tickets, total 52.50")
    code, _, err = cli(capsys, data, "2026-04-01T10:05", "hold", "HAM-0412E", "A2")
    assert (code, err.strip()) == (1, "error: seat A2 is not available")
