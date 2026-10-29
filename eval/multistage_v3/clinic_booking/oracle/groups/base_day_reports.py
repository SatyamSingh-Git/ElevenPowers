import csv
import json
from datetime import date, datetime, time

from clinicbook.cli.main import main
from clinicbook.clock import FixedClock
from clinicbook.reports.day_schedule import export_day
from clinicbook.reports.utilisation import room_utilisation
from clinicbook.services.desk import Desk
from clinicbook.storage.bookings_file import load_bookings, save_bookings
from clinicbook.storage.clinic_file import load_clinic

MONDAY = date(2026, 3, 2)
START = datetime(2026, 2, 27, 8, 0)
CLINIC = {
    "name": "Riverside Physio",
    "rooms": [{"id": "R1", "name": "Room 1"}, {"id": "R2", "name": "Room 2"}, {"id": "R3", "name": "Gym"}],
    "practitioners": [
        {"id": "amy", "name": "Amy Hart", "specialty": "physiotherapy", "room": "R1",
         "days": ["mon", "tue", "wed", "thu", "fri"]},
        {"id": "ben", "name": "Ben Okafor", "specialty": "osteopathy", "room": "R2", "days": ["mon", "wed", "fri"]},
        {"id": "cara", "name": "Cara Diaz", "specialty": "massage", "room": "R3", "days": ["tue", "thu", "sat"]},
    ],
    "hours": {"mon": "09:00-17:00", "tue": "09:00-17:00", "wed": "09:00-17:00", "thu": "09:00-17:00",
              "fri": "09:00-17:00", "sat": "09:00-13:00", "sun": None},
}


def at(text):
    return time.fromisoformat(text)


def write_clinic(folder, **settings):
    path = folder / "clinic.json"
    path.write_text(json.dumps(dict(CLINIC, settings=settings)), encoding="utf-8")
    return path


def cli(folder, *argv, now="2026-02-27T08:00"):
    return main(["--clinic", str(folder / "clinic.json"), "--bookings", str(folder / "bookings.csv"),
                 "--now", now, *argv])


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def busy_monday(folder):
    """A Monday booked out of time order, with one attended, one no-show and one cancelled that morning."""
    clinic = load_clinic(write_clinic(folder))
    clock = FixedClock(START)
    desk = Desk(clinic, [], clock)
    desk.book("amy", MONDAY, at("14:00"), "Dee Fox", "07700900004")
    desk.book("ben", MONDAY, at("10:40"), "Bob Ray", "07700900002")
    desk.book("amy", MONDAY, at("09:00"), "Ann Lee", "07700900001")
    desk.book("amy", MONDAY, at("15:40"), "Eve Gray", "07700900005")
    desk.book("ben", MONDAY, at("12:20"), "Cy Tan", "07700900003")
    desk.book("amy", date(2026, 3, 3), at("09:00"), "Fay Holt", "07700900006")
    clock.moment = datetime(2026, 3, 2, 12, 0)
    desk.cancel("B0004")
    desk.mark_attended("B0003")
    desk.mark_no_show("B0002")
    path = folder / "bookings.csv"
    save_bookings(desk.bookings, path)
    return clinic, path


def test_utilisation_from_the_exported_schedule(tmp_path):
    clinic, path = busy_monday(tmp_path)
    export = tmp_path / "day.csv"
    export_day(load_bookings(path), clinic, MONDAY, export)
    loads = {load.room: (load.booked_minutes, load.open_minutes) for load in room_utilisation(export, clinic)}
    assert loads == {"R1": (40, 480), "R2": (40, 480), "R3": (0, 480)}


def test_export_reads_through_the_day_in_time_order(tmp_path):
    clinic, path = busy_monday(tmp_path)
    export = tmp_path / "day.csv"
    assert export_day(load_bookings(path), clinic, MONDAY, export) == 5
    rows = read_rows(export)
    assert [row["patient"] for row in rows] == ["Ann Lee", "Bob Ray", "Cy Tan", "Dee Fox", "Eve Gray"]
    assert [row["practitioner"] for row in rows] == ["Amy Hart", "Ben Okafor", "Ben Okafor", "Amy Hart", "Amy Hart"]
    assert {row["date"] for row in rows} == {"2026-03-02"}
    assert [row["room"] for row in rows] == ["R1", "R2", "R2", "R1", "R1"]


def test_schedule_command_feeds_utilisation(tmp_path, capsys):
    write_clinic(tmp_path)
    assert cli(tmp_path, "book", "amy", "2026-03-02", "14:00", "--patient", "Dee Fox", "--phone", "07700900004") == 0
    assert cli(tmp_path, "book", "amy", "2026-03-02", "09:00", "--patient", "Ann Lee", "--phone", "07700900001") == 0
    assert cli(tmp_path, "book", "ben", "2026-03-02", "10:40", "--patient", "Bob Ray", "--phone", "07700900002") == 0
    assert cli(tmp_path, "cancel", "B0001", now="2026-03-02T12:00") == 0
    export = tmp_path / "day.csv"
    assert cli(tmp_path, "schedule", "2026-03-02", "--out", str(export)) == 0
    assert [row["patient"] for row in read_rows(export)] == ["Ann Lee", "Bob Ray", "Dee Fox"]
    loads = {load.room: load.booked_minutes for load in room_utilisation(export, load_clinic(tmp_path / "clinic.json"))}
    assert loads == {"R1": 20, "R2": 20, "R3": 0}
    assert cli(tmp_path, "utilisation", str(export)) == 0
