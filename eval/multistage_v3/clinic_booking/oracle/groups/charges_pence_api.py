import csv
import json
from datetime import date, datetime, time

from clinicbook.clock import FixedClock
from clinicbook.services.desk import Desk
from clinicbook.services.fees import charges, write_charges
from clinicbook.storage.clinic_file import load_clinic

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


def charges_file(folder, **settings):
    path = folder / "clinic.json"
    path.write_text(json.dumps(dict(CLINIC, settings=settings)), encoding="utf-8")
    clinic = load_clinic(path)
    clock = FixedClock(datetime(2026, 2, 27, 8, 0))
    desk = Desk(clinic, [], clock)
    made = [
        desk.book("amy", date(2026, 3, 2), time(9, 0), "Ann Lee", "07700900001"),
        desk.book("ben", date(2026, 3, 2), time(9, 0), "Bob Ray", "07700900002"),
        desk.book("amy", date(2026, 3, 4), time(9, 0), "Ann Lee", "07700900001"),
        desk.book("ben", date(2026, 3, 4), time(9, 0), "Bob Ray", "07700900002"),
    ]
    clock.moment = datetime(2026, 3, 4, 18, 0)
    for booking in made:
        desk.mark_no_show(booking.id)
    target = folder / "charges.csv"
    write_charges(charges(desk.bookings, clinic.settings), target)
    with open(target, newline="", encoding="utf-8") as handle:
        return list(csv.reader(handle))


def charged(rows):
    return [row for row in rows[1:] if row[5] != "0"]


def test_charges_file_holds_whole_pence(tmp_path):
    rows = charges_file(tmp_path)
    assert rows[0] == ["booking", "patient", "phone", "day", "reason", "amount_pence"]
    assert charged(rows)
    assert {row[5] for row in charged(rows)} == {"2500"}
    assert {row[4] for row in charged(rows)} == {"no-show"}


def test_pence_follow_the_fee_setting(tmp_path):
    rows = charges_file(tmp_path, no_show_fee="12.50")
    assert charged(rows)
    assert {row[5] for row in charged(rows)} == {"1250"}
