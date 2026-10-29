from datetime import date, datetime

import pytest

from clinicbook.errors import BookingError, NotFound, ValidationError
from clinicbook.services.validation import check_name, check_phone
from conftest import MONDAY, SUNDAY, at


def test_booking_takes_one_slot(desk):
    booking = desk.book("amy", MONDAY, at("09:00"), "  Ann   Lee ", "07700900001")
    assert booking.id == "B0001"
    assert booking.patient == "Ann Lee"
    assert (booking.room, booking.minutes, booking.status) == ("R1", 20, "booked")
    assert booking.created == datetime(2026, 2, 27, 8, 0)


def test_practitioner_cannot_be_booked_twice(desk):
    desk.book("amy", MONDAY, at("10:40"), "Ann Lee", "07700900001")
    with pytest.raises(BookingError, match="Amy Hart is already booked at 10:40"):
        desk.book("amy", MONDAY, at("10:40"), "Bob Ray", "07700900002")


@pytest.mark.parametrize("day, start, message", [
    (SUNDAY, "10:00", "clinic is closed on 2026-03-01"),
    (date(2026, 3, 20), "10:00", "clinic is closed on 2026-03-20"),
    (date(2026, 3, 3), "10:00", "Ben Okafor does not work on Tuesdays"),
    (MONDAY, "08:40", "08:40 is outside opening hours"),
    (MONDAY, "16:50", "16:50 is outside opening hours"),
    (MONDAY, "09:10", "09:10 is not a slot start"),
    (date(2026, 2, 26), "10:00", "cannot book in the past"),
    (date(2026, 6, 1), "10:00", "bookings open 60 days ahead"),
])
def test_rules_on_when(desk, day, start, message):
    with pytest.raises(BookingError) as caught:
        desk.book("ben", day, at(start), "Ann Lee", "07700900001")
    assert str(caught.value) == message


def test_cancelled_booking_frees_the_slot(desk):
    first = desk.book("amy", MONDAY, at("09:00"), "Ann Lee", "07700900001")
    assert desk.cancel(first.id).status == "cancelled"
    second = desk.book("amy", MONDAY, at("09:00"), "Bob Ray", "07700900002")
    assert second.id == "B0002"


def test_only_booked_appointments_can_change(desk, clock):
    booking = desk.book("amy", MONDAY, at("09:00"), "Ann Lee", "07700900001")
    with pytest.raises(BookingError, match="B0001 has not started yet"):
        desk.mark_no_show(booking.id)
    clock.moment = datetime(2026, 3, 2, 12, 0)
    desk.mark_attended(booking.id)
    with pytest.raises(BookingError, match="booking B0001 is attended"):
        desk.cancel(booking.id)


def test_unknown_booking_and_practitioner(desk):
    with pytest.raises(NotFound, match="no booking B0009"):
        desk.cancel("B0009")
    with pytest.raises(NotFound, match="no practitioner zed"):
        desk.book("zed", MONDAY, at("09:00"), "Ann Lee", "07700900001")


def test_patient_details():
    assert check_name(" Ann  Lee ") == "Ann Lee"
    assert check_phone(" 07700900001 ") == "07700900001"
    with pytest.raises(ValidationError, match="patient name is required"):
        check_name("   ")
    with pytest.raises(ValidationError, match="longer than 60"):
        check_name("x" * 61)
    with pytest.raises(ValidationError, match="invalid phone number"):
        check_phone("7700900001")
