from datetime import date, timedelta

import pytest

from hoteldesk.errors import InvalidState, NotFound, Unavailable, ValidationError
from hoteldesk.services import booking, pricing

MONDAY = date(2026, 3, 2)


def book(hotel, settings, **overrides):
    values = {"guest": "Ann Lee", "room_type": "QN", "arrival": MONDAY, "departure": MONDAY + timedelta(days=2)}
    values.update(overrides)
    return booking.book(hotel, settings, **values)


def test_booking_prices_each_night(hotel, settings):
    reservation = book(hotel, settings, departure=date(2026, 3, 9))
    # Friday and Saturday nights carry the 10% uplift.
    assert reservation.rates == [12000, 12000, 12000, 12000, 13200, 13200, 12000]
    assert reservation.status == "booked"


def test_rate_plan_discount(hotel, settings):
    reservation = book(hotel, settings, rate_plan="AAA")
    assert reservation.rates == [10800, 10800]


def test_reservation_numbers_follow_booking_order(hotel, settings):
    first = book(hotel, settings)
    second = book(hotel, settings, guest="Bo Chen")
    booking.cancel(hotel, first.id)
    third = book(hotel, settings, guest="Cy Diaz")
    assert [first.id, second.id, third.id] == ["R0001", "R0002", "R0003"]


@pytest.mark.parametrize("overrides, message", [
    ({"guest": "  "}, "Guest name is required"),
    ({"room_type": "XX"}, "Unknown room type: XX"),
    ({"rate_plan": "NOPE"}, "Unknown rate plan: NOPE"),
    ({"departure": MONDAY}, "Departure must be after arrival"),
    ({"arrival": date(2026, 3, 1)}, "Arrival 2026-03-01 is before the business date 2026-03-02"),
    ({"departure": MONDAY + timedelta(days=31)}, "Stays are limited to 30 nights"),
    ({"rate_plan": "WEEK"}, "Rate plan WEEK requires at least 7 nights"),
    ({"adults": 3}, "Room type QN holds at most 2 adults"),
])
def test_booking_rules(hotel, settings, overrides, message):
    with pytest.raises((ValidationError, NotFound), match=f"^{message}$"):
        book(hotel, settings, **overrides)


def test_sold_out(hotel, settings):
    book(hotel, settings)
    book(hotel, settings, guest="Bo Chen")
    with pytest.raises(Unavailable, match="No QN rooms available on 2026-03-02"):
        book(hotel, settings, guest="Cy Diaz")


def test_cancelled_rooms_go_back_on_sale(hotel, settings):
    first = book(hotel, settings)
    book(hotel, settings, guest="Bo Chen")
    booking.cancel(hotel, first.id)
    assert book(hotel, settings, guest="Cy Diaz").id == "R0003"


def test_only_booked_reservations_cancel(hotel, settings):
    reservation = book(hotel, settings)
    booking.cancel(hotel, reservation.id)
    with pytest.raises(InvalidState, match="Reservation R0001 is cancelled and cannot be cancelled"):
        booking.cancel(hotel, reservation.id)


def test_change_dates_reprices(hotel, settings):
    reservation = book(hotel, settings)
    booking.change_dates(hotel, settings, reservation.id, date(2026, 3, 6), date(2026, 3, 8))
    assert reservation.rates == [13200, 13200]


def test_quote_matches_booking(hotel, settings):
    offer = pricing.quote(hotel, settings, "QN", "BAR", MONDAY, MONDAY + timedelta(days=2))
    assert offer.rates == book(hotel, settings).rates
    assert offer.tax == 2820
    assert offer.total == 26820
