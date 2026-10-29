from datetime import date, datetime

import pytest

from hoteldesk.errors import BalanceDue, InvalidState, RoomNotReady, Unavailable
from hoteldesk.services import billing, booking, housekeeping, stays

MONDAY = date(2026, 3, 2)


@pytest.fixture
def reservation(hotel, settings):
    return booking.book(hotel, settings, guest="Ann Lee", room_type="QN", arrival=MONDAY,
                        departure=date(2026, 3, 4))


def test_check_in_takes_lowest_ready_room(hotel, clock, reservation):
    housekeeping.set_status(hotel, "101", "dirty")
    room = stays.check_in(hotel, clock, reservation.id)
    assert room.number == "102"
    assert reservation.status == "in_house"
    assert reservation.checked_in_at == clock.now()
    assert hotel.folio(reservation.id).balance == 0


def test_check_in_to_a_chosen_room(hotel, clock, reservation):
    room = stays.check_in(hotel, clock, reservation.id, "102")
    assert room.occupied and reservation.room == "102"


def test_check_in_refuses_an_occupied_room(hotel, settings, clock, reservation):
    other = booking.book(hotel, settings, guest="Bo Chen", room_type="QN", arrival=MONDAY,
                         departure=date(2026, 3, 3))
    stays.check_in(hotel, clock, other.id, "101")
    with pytest.raises(RoomNotReady, match="Room 101 is occupied"):
        stays.check_in(hotel, clock, reservation.id, "101")


def test_no_ready_room(hotel, clock, reservation):
    housekeeping.set_status(hotel, "101", "dirty")
    housekeeping.set_status(hotel, "102", "out_of_order")
    with pytest.raises(Unavailable, match="No QN room is ready"):
        stays.check_in(hotel, clock, reservation.id)


def test_check_in_only_on_arrival_day(hotel, settings, clock):
    later = booking.book(hotel, settings, guest="Bo Chen", room_type="KG", arrival=date(2026, 3, 5),
                         departure=date(2026, 3, 6))
    with pytest.raises(InvalidState, match="Reservation R0001 arrives on 2026-03-05"):
        stays.check_in(hotel, clock, later.id)


def test_check_out_needs_a_settled_folio(hotel, settings, clock, reservation):
    stays.check_in(hotel, clock, reservation.id)
    billing.post_charge(hotel, reservation.id, "PH", 300)
    clock.set(datetime(2026, 3, 2, 9, 0))
    with pytest.raises(BalanceDue, match="Balance due: 3.00"):
        stays.check_out(hotel, settings, clock, reservation.id)
    billing.post_payment(hotel, reservation.id, 300, "cash")
    stays.check_out(hotel, settings, clock, reservation.id)
    assert reservation.status == "checked_out"
    assert hotel.room("101").status == "dirty" and not hotel.room("101").occupied


def test_early_departure_gives_up_the_remaining_nights(hotel, settings, clock, reservation):
    stays.check_in(hotel, clock, reservation.id)
    clock.set(datetime(2026, 3, 2, 10, 0))
    stays.check_out(hotel, settings, clock, reservation.id)
    assert reservation.departure == MONDAY and reservation.rates == []


def test_late_check_out_is_charged_once(hotel, settings, clock):
    one_night = booking.book(hotel, settings, guest="Cy Diaz", room_type="ST",
                             arrival=MONDAY, departure=date(2026, 3, 3))
    stays.check_in(hotel, clock, one_night.id)
    hotel.business_date = date(2026, 3, 3)
    clock.set(datetime(2026, 3, 3, 13, 0))
    with pytest.raises(BalanceDue):
        stays.check_out(hotel, settings, clock, one_night.id)
    with pytest.raises(BalanceDue):
        stays.check_out(hotel, settings, clock, one_night.id)
    late = [c for c in hotel.folio(one_night.id).charges if c.code == "LCO"]
    assert len(late) == 1 and late[0].description == "Late check-out"


def test_extend_stay(hotel, settings, clock, reservation):
    stays.check_in(hotel, clock, reservation.id)
    stays.extend_stay(hotel, settings, reservation.id, date(2026, 3, 7))
    assert reservation.rates == [12000, 12000, 12000, 12000, 13200]


def test_move_room(hotel, clock, reservation):
    stays.check_in(hotel, clock, reservation.id)
    stays.move_room(hotel, reservation.id, "102")
    assert reservation.room == "102"
    assert hotel.room("101").status == "dirty" and not hotel.room("101").occupied
