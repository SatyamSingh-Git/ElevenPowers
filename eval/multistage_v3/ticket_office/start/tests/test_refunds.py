from datetime import datetime

import pytest

from boxoffice.errors import BoxOfficeError


def sell(office, seats, concessions=None):
    return office.sales.checkout(office.holds.place("TEMP-0520", seats).id, concessions)


def test_refund_some_seats(office):
    order = sell(office, ["A1", "A2"], {"A2": "child"})
    assert office.refunds.refund(order.id, ["A2"]) == 1500
    assert office.seat_states("TEMP-0520")["A2"] == "free"
    entry = office.ledger.read_entries()[-1]
    assert (entry["kind"], entry["amount"], entry["tickets"]) == ("refund", -1500, 1)


def test_refund_whole_order_keeps_the_fee(office):
    order = sell(office, ["A1", "A2"])
    assert office.refunds.refund(order.id) == 6000


def test_refund_of_a_seat_not_in_the_order(office):
    order = sell(office, ["A1"])
    with pytest.raises(BoxOfficeError) as raised:
        office.refunds.refund(order.id, ["A2"])
    assert str(raised.value) == "seat A2 is not in order B0001"


def test_refunds_close_before_the_performance(office, clock):
    order = sell(office, ["A1"])
    clock.set(datetime(2026, 5, 18, 19, 31))
    with pytest.raises(BoxOfficeError) as raised:
        office.refunds.refund(order.id)
    assert str(raised.value) == "refunds close 48 hours before the performance"


def test_exchange_to_another_performance(office):
    office.schedule.add("TEMP-0521", "The Tempest", datetime(2026, 5, 21, 19, 30), {"A": 3500, "B": 2000})
    order = sell(office, ["C1", "C2"], {"C2": "child"})
    assert office.refunds.exchange(order.id, "TEMP-0521", ["A2", "A1"]) == 5250 - 3000
    moved = office.order(order.id)
    assert moved.performance == "TEMP-0521"
    assert [(line.seat, line.concession) for line in moved.lines] == [("A1", "adult"), ("A2", "child")]
    assert office.seat_states("TEMP-0520")["C1"] == "free"
    assert office.seat_states("TEMP-0521")["A1"] == "sold"


def test_exchange_needs_one_seat_per_ticket(office):
    order = sell(office, ["A1", "A2"])
    with pytest.raises(BoxOfficeError) as raised:
        office.refunds.exchange(order.id, "TEMP-0520", ["A5"])
    assert str(raised.value) == "an exchange needs 2 seats"


def test_exchange_within_a_performance_may_reuse_seats(office):
    order = sell(office, ["A1", "A2"])
    assert office.refunds.exchange(order.id, "TEMP-0520", ["A2", "A3"]) == 0
    assert [line.seat for line in office.order(order.id).lines] == ["A2", "A3"]


def test_cancel_refunds_everything(office):
    order = sell(office, ["A1", "A2"])
    office.refunds.refund(order.id, ["A1"])
    assert office.refunds.cancel_performance("TEMP-0520") == (1, 3150)
    with pytest.raises(BoxOfficeError) as raised:
        office.holds.place("TEMP-0520", ["A1"])
    assert raised.value.code == "performance-cancelled"
