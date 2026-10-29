"""Stage 5: check_in names the housekeeping status of a room that is not ready."""
from datetime import date, datetime

import pytest

from hoteldesk.clock import FixedClock
from hoteldesk.config import Settings
from hoteldesk.errors import HotelError
from hoteldesk.services import booking, housekeeping, stays
from hoteldesk.storage.setup import build_hotel

MONDAY = date(2026, 3, 2)
SETUP = {
    "name": "Harbour View Inn",
    "room_types": [{"code": "QN", "name": "Queen", "max_adults": 2, "base_rate": "120.00"}],
    "rooms": [{"number": "101", "type": "QN"}, {"number": "102", "type": "QN"}, {"number": "103", "type": "QN"}],
    "rate_plans": [{"code": "BAR", "name": "Best available"}],
}


def _arrival():
    hotel = build_hotel(SETUP, MONDAY)
    reservation = booking.book(hotel, Settings(), guest="Ann Lee", room_type="QN", arrival=MONDAY,
                               departure=date(2026, 3, 3))
    return hotel, FixedClock(datetime(2026, 3, 2, 15, 0)), reservation


def test_dirty_room():
    hotel, clock, reservation = _arrival()
    housekeeping.set_status(hotel, "102", "dirty")
    with pytest.raises(HotelError, match="^Room 102 is not ready: dirty$"):
        stays.check_in(hotel, clock, reservation.id, "102")
    assert reservation.status == "booked"


def test_out_of_order_room():
    hotel, clock, reservation = _arrival()
    housekeeping.set_status(hotel, "103", "out_of_order")
    with pytest.raises(HotelError, match="^Room 103 is not ready: out_of_order$"):
        stays.check_in(hotel, clock, reservation.id, "103")


def test_ready_rooms_still_check_in():
    hotel, clock, reservation = _arrival()
    housekeeping.set_status(hotel, "102", "inspected")
    assert stays.check_in(hotel, clock, reservation.id, "102").number == "102"
