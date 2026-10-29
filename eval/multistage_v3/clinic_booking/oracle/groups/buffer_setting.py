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
    "rooms": [{"id": "R1", "name": "Room 1"}],
    "practitioners": [
        {"id": "amy", "name": "Amy Hart", "specialty": "physiotherapy", "room": "R1",
         "days": ["mon", "tue", "wed", "thu", "fri"]},
    ],
    "hours": {"mon": "09:00-17:00", "tue": "09:00-17:00", "wed": "09:00-17:00", "thu": "09:00-17:00",
              "fri": "09:00-17:00", "sat": None, "sun": None},
}


def load(folder, **settings):
    path = folder / "clinic.json"
    path.write_text(json.dumps(dict(CLINIC, settings=settings)), encoding="utf-8")
    return load_clinic(path)


def test_buffer_minutes_from_the_clinic_file(tmp_path):
    clinic = load(tmp_path, buffer_minutes=10)
    starts = [slot.start for slot in free_slots(clinic, [], MONDAY, START, practitioner="amy")]
    assert starts[:3] == [time(9, 0), time(9, 30), time(10, 0)]
    assert starts[-1] == time(16, 30)
    desk = Desk(clinic, [], FixedClock(START))
    assert desk.book("amy", MONDAY, time(9, 30), "Ann Lee", "07700900001").minutes == 20


def test_zero_buffer_keeps_slots_back_to_back(tmp_path):
    clinic = load(tmp_path, buffer_minutes=0, slot_minutes=30)
    starts = [slot.start for slot in free_slots(clinic, [], MONDAY, START, practitioner="amy")]
    assert starts[:3] == [time(9, 0), time(9, 30), time(10, 0)]
    assert len(starts) == 16
