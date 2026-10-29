import csv
import json
from datetime import date, datetime, time

from clinicbook.clock import FixedClock
from clinicbook.services.desk import Desk
from clinicbook.storage.bookings_file import load_bookings, save_bookings
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


def file_ids(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return [row["id"] for row in csv.DictReader(handle)]


def test_bookings_file_is_in_booking_reference_order(tmp_path):
    clinic_path = tmp_path / "clinic.json"
    clinic_path.write_text(json.dumps(CLINIC), encoding="utf-8")
    clinic = load_clinic(clinic_path)
    desk = Desk(clinic, [], FixedClock(datetime(2026, 2, 27, 8, 0)))
    desk.book("amy", date(2026, 3, 4), time(14, 0), "Ann Lee", "07700900001")
    desk.book("ben", MONDAY, time(9, 0), "Bob Ray", "07700900002")
    desk.book("amy", MONDAY, time(10, 40), "Cy Tan", "07700900003")
    desk.book("amy", MONDAY, time(9, 0), "Dee Fox", "07700900004")
    path = tmp_path / "bookings.csv"
    save_bookings(list(reversed(desk.bookings)), path)
    assert file_ids(path) == ["B0001", "B0002", "B0003", "B0004"]
    reloaded = load_bookings(path)
    later = Desk(clinic, reloaded, FixedClock(datetime(2026, 2, 28, 8, 0)))
    later.book("ben", MONDAY, time(10, 40), "Eve Gray", "07700900005")
    save_bookings(later.bookings, path)
    assert file_ids(path) == ["B0001", "B0002", "B0003", "B0004", "B0005"]
