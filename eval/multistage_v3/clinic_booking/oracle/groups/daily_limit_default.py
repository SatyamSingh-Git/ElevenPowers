import json
from datetime import date, datetime, time

import pytest

from clinicbook.clock import FixedClock
from clinicbook.errors import ClinicError
from clinicbook.services.desk import Desk
from clinicbook.storage.clinic_file import load_clinic

MONDAY = date(2026, 3, 2)
CLINIC = {
    "name": "Riverside Physio",
    "rooms": [{"id": "R1", "name": "Room 1"}, {"id": "R2", "name": "Room 2"}],
    "practitioners": [
        {"id": "amy", "name": "Amy Hart", "specialty": "physiotherapy", "room": "R1",
         "days": ["mon", "tue", "wed", "thu", "fri"]},
        {"id": "ben", "name": "Ben Okafor", "specialty": "osteopathy", "room": "R2", "days": ["mon", "wed", "fri"]},
    ],
    "hours": {"mon": "09:00-17:00", "tue": "09:00-17:00", "wed": "09:00-17:00", "thu": "09:00-17:00",
              "fri": "09:00-17:00", "sat": None, "sun": None},
}


def desk_for(folder):
    path = folder / "clinic.json"
    path.write_text(json.dumps(CLINIC), encoding="utf-8")
    return Desk(load_clinic(path), [], FixedClock(datetime(2026, 2, 27, 8, 0)))


def test_third_booking_on_one_day_is_refused(tmp_path):
    desk = desk_for(tmp_path)
    desk.book("amy", MONDAY, time(9, 0), "Ann Lee", "07700900001")
    desk.book("ben", MONDAY, time(10, 40), "Ann Lee", "07700900001")
    with pytest.raises(ClinicError) as caught:
        desk.book("amy", MONDAY, time(14, 0), "Ann Lee", "07700900001")
    assert str(caught.value) == "Ann Lee already has 2 bookings on 2026-03-02"
    assert len(desk.bookings) == 2


def test_other_days_other_phones_and_cancellations(tmp_path):
    desk = desk_for(tmp_path)
    first = desk.book("amy", MONDAY, time(9, 0), "Ann Lee", "07700900001")
    desk.book("ben", MONDAY, time(10, 40), "Ann Lee", "07700900001")
    desk.book("amy", date(2026, 3, 3), time(9, 0), "Ann Lee", "07700900001")
    desk.book("amy", MONDAY, time(14, 0), "Bob Ray", "07700900002")
    desk.cancel(first.id)
    assert desk.book("amy", MONDAY, time(15, 40), "Ann Lee", "07700900001").day == MONDAY
