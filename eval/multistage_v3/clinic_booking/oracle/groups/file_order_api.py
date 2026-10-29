import csv
import json
from datetime import date, datetime, time

from clinicbook.cli.main import main
from clinicbook.clock import FixedClock
from clinicbook.services.desk import Desk
from clinicbook.storage.bookings_file import save_bookings
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
HEADER = "id,patient,phone,practitioner,room,day,start,minutes,status,created\n"
# Written by day and start time, the way the bookings file used to be kept.
DAY_ORDER = (
    "B0002,Bob Ray,07700900002,ben,R2,2026-03-02,09:00,20,booked,2026-02-26T09:00\n"
    "B0003,Cy Tan,07700900003,amy,R1,2026-03-02,10:40,20,booked,2026-02-26T10:00\n"
    "B0001,Ann Lee,07700900001,amy,R1,2026-03-04,14:00,20,booked,2026-02-26T08:00\n"
)


def file_ids(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return [row["id"] for row in csv.DictReader(handle)]


def write_clinic(folder):
    path = folder / "clinic.json"
    path.write_text(json.dumps(CLINIC), encoding="utf-8")
    return path


def test_bookings_made_out_of_time_order_are_saved_oldest_first(tmp_path):
    clinic = load_clinic(write_clinic(tmp_path))
    desk = Desk(clinic, [], FixedClock(datetime(2026, 2, 27, 8, 0)))
    desk.book("amy", date(2026, 3, 4), time(14, 0), "Ann Lee", "07700900001")
    desk.book("ben", MONDAY, time(9, 0), "Bob Ray", "07700900002")
    desk.book("amy", MONDAY, time(10, 40), "Cy Tan", "07700900003")
    desk.book("amy", MONDAY, time(9, 0), "Dee Fox", "07700900004")
    path = tmp_path / "bookings.csv"
    save_bookings(desk.bookings, path)
    assert file_ids(path) == ["B0001", "B0002", "B0003", "B0004"]


def test_a_file_kept_in_day_order_is_rewritten_oldest_first(tmp_path):
    write_clinic(tmp_path)
    path = tmp_path / "bookings.csv"
    path.write_text(HEADER + DAY_ORDER, encoding="utf-8")
    argv = ["--clinic", str(tmp_path / "clinic.json"), "--bookings", str(path), "--now", "2026-02-27T08:00",
            "book", "ben", "2026-03-02", "12:20", "--patient", "Eve Gray", "--phone", "07700900005"]
    assert main(argv) == 0
    assert file_ids(path) == ["B0001", "B0002", "B0003", "B0004"]
