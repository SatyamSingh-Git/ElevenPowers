"""A guest's stay end to end: quote, booking, check-in, nightly posting, the printed folio, numbering."""
from datetime import date, datetime, timedelta

from hoteldesk.clock import FixedClock
from hoteldesk.config import Settings
from hoteldesk.reports.folio_print import print_folio
from hoteldesk.services import billing, booking, night_audit, pricing, stays
from hoteldesk.storage.setup import build_hotel

MONDAY = date(2026, 3, 2)
SETUP = {
    "name": "Harbour View Inn",
    "room_types": [
        {"code": "QN", "name": "Queen", "max_adults": 2, "base_rate": "120.00"},
        {"code": "KG", "name": "King", "max_adults": 2, "base_rate": "150.00"},
        {"code": "ST", "name": "Suite", "max_adults": 4, "base_rate": "260.00"},
    ],
    "rooms": [
        {"number": "101", "type": "QN"},
        {"number": "102", "type": "QN"},
        {"number": "201", "type": "KG"},
        {"number": "202", "type": "KG"},
        {"number": "301", "type": "ST"},
    ],
    "rate_plans": [
        {"code": "BAR", "name": "Best available"},
        {"code": "AAA", "name": "Motoring club", "discount_percent": 10, "breakfast": True},
    ],
}


def _stay(nights, room_type="KG"):
    hotel = build_hotel(SETUP, MONDAY)
    settings = Settings()
    clock = FixedClock(datetime(2026, 3, 2, 15, 30))
    departure = MONDAY + timedelta(days=nights)
    offer = pricing.quote(hotel, settings, room_type, "BAR", MONDAY, departure)
    reservation = booking.book(hotel, settings, guest="Ann Lee", room_type=room_type, arrival=MONDAY,
                               departure=departure)
    stays.check_in(hotel, clock, reservation.id)
    for _ in range(nights):
        night_audit.run_audit(hotel, settings)
    return hotel, settings, clock, offer, reservation


def test_quote_equals_what_the_stay_posts():
    hotel, _, _, offer, reservation = _stay(7)
    folio = hotel.folio(reservation.id)
    assert offer.rates == reservation.rates
    assert sum(charge.amount for charge in folio.charges) == offer.total
    taxes = [charge.amount for charge in folio.charges if charge.code == "TAX"]
    assert sum(taxes) == offer.tax


def test_quote_equals_posted_for_a_queen_too():
    hotel, _, _, offer, reservation = _stay(3, "QN")
    assert hotel.folio(reservation.id).charged == offer.total


def test_printed_folio_puts_room_nights_under_accommodation():
    hotel, settings, clock, _, reservation = _stay(3)
    billing.post_charge(hotel, reservation.id, "PH", 450)
    lines = print_folio(hotel, reservation.id).splitlines()
    accommodation = lines.index("Accommodation")
    taxes = lines.index("Taxes")
    extras = lines.index("Extras")
    assert accommodation < taxes < extras
    nights = [line for line in lines[accommodation + 1:taxes] if "night of" in line]
    assert len(nights) == 3
    assert "2026-03-02" in nights[0] and "2026-03-04" in nights[2]
    assert not any("night of" in line for line in lines[extras:])
    assert any("Telephone" in line for line in lines[extras:])


def test_settled_stay_checks_out():
    hotel, settings, clock, offer, reservation = _stay(2)
    billing.post_payment(hotel, reservation.id, hotel.folio(reservation.id).balance, "card")
    clock.set(datetime(2026, 3, 4, 10, 15))
    stays.check_out(hotel, settings, clock, reservation.id)
    assert reservation.status == "checked_out"
    assert hotel.room(reservation.room).status == "dirty"


def test_reservation_numbers_are_never_reused_over_a_month():
    hotel = build_hotel(SETUP, MONDAY)
    settings = Settings()
    first = booking.book(hotel, settings, guest="Ann Lee", room_type="QN", arrival=date(2026, 3, 3),
                         departure=date(2026, 3, 5))
    second = booking.book(hotel, settings, guest="Bo Chen", room_type="KG", arrival=date(2026, 4, 20),
                          departure=date(2026, 4, 22))
    booking.cancel(hotel, first.id)
    for _ in range(40):
        night_audit.run_audit(hotel, settings)
    assert hotel.business_date == date(2026, 4, 11)
    third = booking.book(hotel, settings, guest="Cy Diaz", room_type="KG", arrival=date(2026, 4, 12),
                         departure=date(2026, 4, 13))
    assert (first.id, second.id, third.id) == ("R0001", "R0002", "R0003")
    assert hotel.reservation("R0002").guest == "Bo Chen"
    assert hotel.reservation("R0002").arrival == date(2026, 4, 20)
    assert hotel.reservation("R0003").guest == "Cy Diaz"
