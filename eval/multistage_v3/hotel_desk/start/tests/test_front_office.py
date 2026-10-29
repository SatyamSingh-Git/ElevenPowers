from datetime import date, datetime

import pytest

from hoteldesk.errors import InvalidState, ValidationError
from hoteldesk.services import booking, desk_log, guests, housekeeping, rooms_admin, stays

MONDAY = date(2026, 3, 2)


def test_housekeeping_status(hotel):
    housekeeping.set_status(hotel, "101", "dirty")
    assert hotel.room("101").status == "dirty"
    with pytest.raises(ValidationError, match="Unknown housekeeping status: sparkling"):
        housekeeping.set_status(hotel, "101", "sparkling")


def test_cleaning_list(hotel, settings, clock):
    reservation = booking.book(hotel, settings, guest="Ann Lee", room_type="QN", arrival=MONDAY,
                               departure=date(2026, 3, 4))
    stays.check_in(hotel, clock, reservation.id)
    housekeeping.set_status(hotel, "201", "dirty")
    housekeeping.set_status(hotel, "202", "inspected")
    housekeeping.set_status(hotel, "301", "out_of_order")
    assert housekeeping.tasks(hotel) == [("201", "clean"), ("101", "stayover"), ("102", "inspect")]


def test_attendant_sheets(hotel):
    for number in ("101", "102", "201"):
        housekeeping.set_status(hotel, number, "dirty")
    sheets = housekeeping.assign(hotel, ["Ines", "Joao"])
    assert sheets == {"Ines": [("101", "clean"), ("102", "clean"), ("201", "clean")],
                      "Joao": [("202", "inspect"), ("301", "inspect")]}


def test_guest_profiles(hotel, settings):
    guests.save_profile(hotel, "Ann Lee", email="ann@example.com")
    guests.save_profile(hotel, "Ann Lee", vip=True)
    assert hotel.guest("Ann Lee").email == "ann@example.com" and guests.is_vip(hotel, "Ann Lee")
    assert [g.name for g in guests.find(hotel, "ann")] == ["Ann Lee"]
    with pytest.raises(ValidationError, match="Not an email address: ann"):
        guests.save_profile(hotel, "Ann Lee", email="ann")


def test_wake_up_calls(hotel, settings, clock):
    reservation = booking.book(hotel, settings, guest="Ann Lee", room_type="QN", arrival=MONDAY,
                               departure=date(2026, 3, 4))
    stays.check_in(hotel, clock, reservation.id)
    desk_log.book_wake_up(hotel, clock, "101", datetime(2026, 3, 3, 6, 30))
    clock.set(datetime(2026, 3, 3, 6, 20))
    assert [call.room for call in desk_log.calls_due(hotel, clock)] == ["101"]
    desk_log.mark_called(hotel, clock, "101")
    assert desk_log.calls_due(hotel, clock) == []
    with pytest.raises(InvalidState, match="Room 102 is not occupied"):
        desk_log.book_wake_up(hotel, clock, "102", datetime(2026, 3, 3, 7, 0))


def test_lost_property(hotel):
    item = desk_log.log_lost_item(hotel, "Room 101", "Blue umbrella")
    desk_log.return_item(hotel, item.number, "Ann Lee")
    with pytest.raises(InvalidState, match="Item 1 is already returned"):
        desk_log.return_item(hotel, item.number, "Bo Chen")


def test_retyping_a_room_keeps_bookings_whole(hotel, settings):
    booking.book(hotel, settings, guest="Ann Lee", room_type="QN", arrival=MONDAY, departure=date(2026, 3, 4))
    booking.book(hotel, settings, guest="Bo Chen", room_type="QN", arrival=MONDAY, departure=date(2026, 3, 3))
    with pytest.raises(InvalidState, match="Room 102 is needed for QN bookings on 2026-03-02"):
        rooms_admin.change_room_type(hotel, "102", "KG")
    assert hotel.room("102").type_code == "QN"


def test_reinstate_a_no_show(hotel, settings):
    reservation = booking.book(hotel, settings, guest="Ann Lee", room_type="QN", arrival=MONDAY,
                               departure=date(2026, 3, 4))
    reservation.status = "no_show"
    hotel.business_date = date(2026, 3, 3)
    booking.reinstate(hotel, reservation.id)
    assert reservation.status == "booked"
    assert reservation.arrival == date(2026, 3, 3) and reservation.rates == [12000]
