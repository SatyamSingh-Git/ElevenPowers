import json
from datetime import date, datetime, time
from decimal import Decimal

from clinicbook.clock import FixedClock
from clinicbook.services.desk import Desk
from clinicbook.services.fees import charges
from clinicbook.storage.clinic_file import load_clinic

CLINIC = {
    "name": "Riverside Physio",
    "rooms": [{"id": "R1", "name": "Room 1"}],
    "practitioners": [
        {"id": "amy", "name": "Amy Hart", "specialty": "physiotherapy", "room": "R1",
         "days": ["mon", "tue", "wed", "thu", "fri"]},
    ],
    "hours": {"mon": "09:00-17:00", "tue": "09:00-17:00", "wed": "09:00-17:00", "thu": "09:00-17:00",
              "fri": "09:00-17:00", "sat": None, "sun": None},
}


def owed_with(folder, **settings):
    path = folder / "clinic.json"
    path.write_text(json.dumps(dict(CLINIC, settings=settings)), encoding="utf-8")
    clinic = load_clinic(path)
    clock = FixedClock(datetime(2026, 2, 27, 8, 0))
    desk = Desk(clinic, [], clock)
    made = [
        desk.book("amy", date(2026, 3, 2), time(9, 0), "Ann Lee", "07700900001"),
        desk.book("amy", date(2026, 3, 3), time(9, 0), "Ann Lee", "07700900001"),
        desk.book("amy", date(2026, 3, 2), time(10, 40), "Bob Ray", "07700900002"),
    ]
    clock.moment = datetime(2026, 3, 3, 18, 0)
    for booking in made:
        desk.mark_no_show(booking.id)
    return charges(desk.bookings, clinic.settings), made


def test_with_the_setting_off_every_no_show_is_charged(tmp_path):
    owed, made = owed_with(tmp_path, first_no_show_free=False)
    assert sorted(charge.booking for charge in owed) == sorted(booking.id for booking in made)
    assert {charge.amount for charge in owed} == {Decimal("25.00")}


def test_with_the_setting_on_only_repeat_no_shows_are_charged(tmp_path):
    owed, made = owed_with(tmp_path, first_no_show_free=True)
    assert [charge.booking for charge in owed] == [made[1].id]
