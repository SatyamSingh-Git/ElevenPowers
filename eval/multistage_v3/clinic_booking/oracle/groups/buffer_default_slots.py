import json
from datetime import date, datetime, time

from clinicbook.clock import FixedClock
from clinicbook.services.availability import free_slots
from clinicbook.services.desk import Desk
from clinicbook.storage.clinic_file import load_clinic

MONDAY = date(2026, 3, 2)
START = datetime(2026, 2, 27, 8, 0)
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


def load(folder):
    path = folder / "clinic.json"
    path.write_text(json.dumps(CLINIC), encoding="utf-8")
    return load_clinic(path)


def test_default_buffer_leaves_five_minutes_after_each_slot(tmp_path):
    clinic = load(tmp_path)
    starts = [slot.start for slot in free_slots(clinic, [], MONDAY, START, practitioner="amy")]
    assert starts[:4] == [time(9, 0), time(9, 25), time(9, 50), time(10, 15)]
    assert starts[-1] == time(16, 30)
    assert all(slot.minutes == 20 for slot in free_slots(clinic, [], MONDAY, START, practitioner="amy"))


def test_buffered_slot_can_be_booked_and_keeps_its_length(tmp_path):
    clinic = load(tmp_path)
    desk = Desk(clinic, [], FixedClock(START))
    booking = desk.book("amy", MONDAY, time(9, 25), "Ann Lee", "07700900001")
    assert (booking.start, booking.minutes, booking.end) == (time(9, 25), 20, time(9, 45))
    starts = [slot.start for slot in free_slots(clinic, desk.bookings, MONDAY, START, practitioner="amy")]
    assert time(9, 25) not in starts
    assert time(9, 50) in starts
