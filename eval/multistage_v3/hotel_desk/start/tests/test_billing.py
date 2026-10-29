from datetime import date

import pytest

from hoteldesk.errors import InvalidState, ValidationError
from hoteldesk.services import billing, booking, stays

MONDAY = date(2026, 3, 2)


@pytest.fixture
def guest(hotel, settings, clock):
    reservation = booking.book(hotel, settings, guest="Ann Lee", room_type="QN", arrival=MONDAY,
                               departure=date(2026, 3, 4))
    stays.check_in(hotel, clock, reservation.id)
    return reservation


def test_charge_carries_its_tax(hotel, guest):
    posted = billing.post_charge(hotel, guest.id, "FB", 4000)
    assert [(c.code, c.description, c.amount) for c in posted] == [
        ("FB", "Food and beverage", 4000),
        ("TAX", "Tax on Food and beverage", 290),
    ]
    assert hotel.folio(guest.id).balance == 4290


def test_exempt_charge_has_no_tax(hotel, guest):
    posted = billing.post_charge(hotel, guest.id, "ph", 250, "Call to Lisbon")
    assert [(c.code, c.description) for c in posted] == [("PH", "Call to Lisbon")]


def test_unknown_code(hotel, guest):
    with pytest.raises(ValidationError, match="Unknown charge code: ZZ"):
        billing.post_charge(hotel, guest.id, "ZZ", 100)


def test_charges_need_an_in_house_guest(hotel, settings):
    reservation = booking.book(hotel, settings, guest="Bo Chen", room_type="KG", arrival=MONDAY,
                               departure=date(2026, 3, 3))
    with pytest.raises(InvalidState, match="Reservation R0001 is not in house"):
        billing.post_charge(hotel, reservation.id, "FB", 100)


def test_payments(hotel, guest):
    billing.post_charge(hotel, guest.id, "PK", 2000)
    with pytest.raises(ValidationError, match="Unknown payment method: cheque"):
        billing.post_payment(hotel, guest.id, 100, "cheque")
    with pytest.raises(ValidationError, match="is more than the balance of 21.45"):
        billing.post_payment(hotel, guest.id, 5000)
    billing.post_payment(hotel, guest.id, 2145, "cash")
    assert hotel.folio(guest.id).balance == 0


def test_transfer_charge(hotel, settings, clock, guest):
    other = booking.book(hotel, settings, guest="Bo Chen", room_type="KG", arrival=MONDAY,
                         departure=date(2026, 3, 3))
    stays.check_in(hotel, clock, other.id)
    billing.post_charge(hotel, guest.id, "PH", 500)
    billing.transfer_charge(hotel, guest.id, 0, other.id)
    assert hotel.folio(guest.id).balance == 0
    assert hotel.folio(other.id).balance == 500
