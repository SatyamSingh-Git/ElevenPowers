import csv
import json
from datetime import date, datetime, time

from clinicbook.clock import FixedClock
from clinicbook.reports.day_schedule import export_day
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


def test_exported_times_use_a_twelve_hour_clock(tmp_path):
    path = tmp_path / "clinic.json"
    path.write_text(json.dumps(CLINIC), encoding="utf-8")
    clinic = load_clinic(path)
    desk = Desk(clinic, [], FixedClock(datetime(2026, 2, 27, 8, 0)))
    desk.book("amy", MONDAY, time(9, 0), "Ann Lee", "07700900001")
    desk.book("ben", MONDAY, time(12, 20), "Bob Ray", "07700900002")
    desk.book("amy", MONDAY, time(14, 0), "Cy Tan", "07700900003")
    export = tmp_path / "day.csv"
    export_day(desk.bookings, clinic, MONDAY, export)
    with open(export, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert [(row["start"], row["end"]) for row in rows] == [
        ("09:00 AM", "09:20 AM"),
        ("12:20 PM", "12:40 PM"),
        ("02:00 PM", "02:20 PM"),
    ]
    assert [row["date"] for row in rows] == ["2026-03-02"] * 3
