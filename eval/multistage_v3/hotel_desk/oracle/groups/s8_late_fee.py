"""Stage 8: a late check-out posts 40.00 by default."""
from datetime import date, datetime

import pytest

from hoteldesk.clock import FixedClock
from hoteldesk.config import Settings
from hoteldesk.errors import HotelError
from hoteldesk.services import billing, booking, night_audit, stays
from hoteldesk.storage.setup import build_hotel

MONDAY = date(2026, 3, 2)
SETUP = {
    "name": "Harbour View Inn",
    "room_types": [{"code": "QN", "name": "Queen", "max_adults": 2, "base_rate": "120.00"}],
    "rooms": [{"number": "101", "type": "QN"}],
    "rate_plans": [{"code": "BAR", "name": "Best available"}],
}


def _due_out():
    hotel = build_hotel(SETUP, MONDAY)
    settings = Settings()
    clock = FixedClock(datetime(2026, 3, 2, 15, 0))
    reservation = booking.book(hotel, settings, guest="Ann Lee", room_type="QN", arrival=MONDAY,
                               departure=date(2026, 3, 3))
    stays.check_in(hotel, clock, reservation.id)
    night_audit.run_audit(hotel, settings)
    billing.post_payment(hotel, reservation.id, hotel.folio(reservation.id).balance)
    return hotel, settings, clock, reservation


def test_late_check_out_posts_40():
    hotel, settings, clock, reservation = _due_out()
    clock.set(datetime(2026, 3, 3, 12, 30))
    with pytest.raises(HotelError, match="^Balance due: 44.70$"):
        stays.check_out(hotel, settings, clock, reservation.id)
    late = [c for c in hotel.folio(reservation.id).charges if c.day == date(2026, 3, 3)]
    assert [(c.code, c.amount) for c in late] == [("LCO", 4000), ("TAX", 470)]
    billing.post_payment(hotel, reservation.id, hotel.folio(reservation.id).balance)
    stays.check_out(hotel, settings, clock, reservation.id)
    assert reservation.status == "checked_out"


def test_on_time_check_out_is_free():
    hotel, settings, clock, reservation = _due_out()
    clock.set(datetime(2026, 3, 3, 10, 59))
    stays.check_out(hotel, settings, clock, reservation.id)
    assert hotel.folio(reservation.id).balance == 0
