"""Stage 2: the 45-night limit holds for channel imports and stay extensions too."""
from datetime import date, datetime

import pytest

from hoteldesk.clock import FixedClock
from hoteldesk.config import Settings
from hoteldesk.errors import HotelError
from hoteldesk.services import booking, stays
from hoteldesk.storage.channel_import import import_bookings
from hoteldesk.storage.setup import build_hotel

MONDAY = date(2026, 3, 2)
SETUP = {
    "name": "Harbour View Inn",
    "room_types": [{"code": "QN", "name": "Queen", "max_adults": 2, "base_rate": "120.00"}],
    "rooms": [{"number": "101", "type": "QN"}, {"number": "102", "type": "QN"}],
    "rate_plans": [{"code": "BAR", "name": "Best available"}],
}


def test_channel_import_takes_45_nights_and_not_46(tmp_path):
    hotel = build_hotel(SETUP, MONDAY)
    path = tmp_path / "channel.csv"
    path.write_text(
        "channel_ref,guest,room_type,arrival,departure,adults,rate_plan\n"
        "BK-7,Ann Lee,QN,2026-03-02,2026-04-16,1,BAR\n"
        "BK-8,Bo Chen,QN,2026-03-02,2026-04-17,1,BAR\n",
        encoding="utf-8",
    )
    result = import_bookings(hotel, Settings(), path)
    assert result.booked == ["R0001"]
    assert hotel.reservation("R0001").nights == 45
    assert result.rejected == [(3, "Stays are limited to 45 nights")]


def test_extension_up_to_45_nights():
    hotel = build_hotel(SETUP, MONDAY)
    settings = Settings()
    clock = FixedClock(datetime(2026, 3, 2, 15, 0))
    reservation = booking.book(hotel, settings, guest="Ann Lee", room_type="QN", arrival=MONDAY,
                               departure=date(2026, 3, 30))
    stays.check_in(hotel, clock, reservation.id)
    stays.extend_stay(hotel, settings, reservation.id, date(2026, 4, 16))
    assert reservation.nights == 45
    with pytest.raises(HotelError, match="^Stays are limited to 45 nights$"):
        stays.extend_stay(hotel, settings, reservation.id, date(2026, 4, 17))
