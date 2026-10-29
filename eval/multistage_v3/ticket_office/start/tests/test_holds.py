from datetime import datetime

import pytest

from boxoffice.errors import BoxOfficeError


def test_hold_puts_seats_in_plan_order(office):
    hold = office.holds.place("TEMP-0520", ["A3", "A1", "A2"])
    assert hold.id == "H0001"
    assert hold.seats == ["A1", "A2", "A3"]
    assert hold.expires == datetime(2026, 5, 1, 10, 15)
    assert office.seat_states("TEMP-0520")["A2"] == "held"


def test_held_seats_cannot_be_held_again(office):
    office.holds.place("TEMP-0520", ["A1"])
    with pytest.raises(BoxOfficeError) as raised:
        office.holds.place("TEMP-0520", ["A2", "A1"])
    assert raised.value.code == "seat-unavailable"


def test_expired_hold_frees_its_seats(office, clock):
    hold = office.holds.place("TEMP-0520", ["A1"])
    clock.set(datetime(2026, 5, 1, 10, 15))
    assert office.seat_states("TEMP-0520")["A1"] == "free"
    with pytest.raises(BoxOfficeError) as raised:
        office.sales.checkout(hold.id)
    assert raised.value.code == "hold-expired"


def test_release(office):
    hold = office.holds.place("TEMP-0520", ["A1"])
    office.holds.release(hold.id)
    assert office.seat_states("TEMP-0520")["A1"] == "free"
    with pytest.raises(BoxOfficeError) as raised:
        office.holds.release(hold.id)
    assert raised.value.code == "hold-closed"


def test_too_many_seats(office):
    seats = [f"A{n}" for n in range(1, 7)] + [f"C{n}" for n in range(1, 5)] + ["B1"]
    with pytest.raises(BoxOfficeError) as raised:
        office.holds.place("TEMP-0520", seats)
    assert str(raised.value) == "at most 10 tickets per order"


def test_unknown_seat(office):
    with pytest.raises(BoxOfficeError) as raised:
        office.holds.place("TEMP-0520", ["Z9"])
    assert str(raised.value) == "unknown seat Z9"


def test_best_available_takes_seats_together(office):
    office.holds.place("TEMP-0520", ["A3"])
    hold = office.holds.place_best("TEMP-0520", 3)
    assert hold.seats == ["A4", "A5", "A6"]
    hold = office.holds.place_best("TEMP-0520", 2, section="circle")
    assert hold.seats == ["C1", "C2"]


def test_best_available_gives_up(office):
    with pytest.raises(BoxOfficeError) as raised:
        office.holds.place_best("TEMP-0520", 5, section="Circle")
    assert str(raised.value) == "no block of 5 seats available"


def test_no_holds_once_started(office, clock):
    clock.set(datetime(2026, 5, 20, 19, 30))
    with pytest.raises(BoxOfficeError) as raised:
        office.holds.place("TEMP-0520", ["A1"])
    assert raised.value.code == "performance-started"


def test_hold_ids_follow_on(office):
    first = office.holds.place("TEMP-0520", ["A1"])
    office.holds.release(first.id)
    assert office.holds.place("TEMP-0520", ["A1"]).id == "H0002"
