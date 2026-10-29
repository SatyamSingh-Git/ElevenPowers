import csv
import json
from datetime import date, datetime, time

from clinicbook.clock import FixedClock
from clinicbook.services.availability import free_slots
from clinicbook.services.desk import Desk
from clinicbook.services.fees import charges
from clinicbook.storage.bookings_file import load_bookings, save_bookings
from clinicbook.storage.clinic_file import load_clinic

MONDAY = date(2026, 3, 2)
WEDNESDAY = date(2026, 3, 4)
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


def setup(folder, **settings):
    path = folder / "clinic.json"
    path.write_text(json.dumps(dict(CLINIC, settings=settings)), encoding="utf-8")
    clinic = load_clinic(path)
    clock = FixedClock(datetime(2026, 2, 27, 8, 0))
    return clinic, clock, Desk(clinic, [], clock)


def test_short_notice_cancellation_is_kept_as_late(tmp_path):
    clinic, clock, desk = setup(tmp_path)
    soon = desk.book("amy", MONDAY, time(9, 0), "Ann Lee", "07700900001")
    later = desk.book("amy", WEDNESDAY, time(9, 0), "Bob Ray", "07700900002")
    clock.moment = datetime(2026, 3, 2, 8, 0)
    assert desk.cancel(soon.id).status == "late_cancelled"
    assert desk.cancel(later.id).status == "cancelled"
    path = tmp_path / "bookings.csv"
    save_bookings(desk.bookings, path)
    with open(path, newline="", encoding="utf-8") as handle:
        statuses = {row["id"]: row["status"] for row in csv.DictReader(handle)}
    assert statuses == {soon.id: "late_cancelled", later.id: "cancelled"}
    assert {b.id: b.status for b in load_bookings(path)} == statuses


def test_late_cancellation_frees_the_slot_and_costs_nothing(tmp_path):
    clinic, clock, desk = setup(tmp_path)
    soon = desk.book("amy", MONDAY, time(10, 40), "Ann Lee", "07700900001")
    clock.moment = datetime(2026, 3, 2, 8, 0)
    assert desk.cancel(soon.id).status == "late_cancelled"
    starts = [slot.start for slot in free_slots(clinic, desk.bookings, MONDAY, clock.now(), practitioner="amy")]
    assert time(10, 40) in starts
    assert charges(desk.bookings, clinic.settings) == []
    assert desk.book("amy", MONDAY, time(10, 40), "Bob Ray", "07700900002").start == time(10, 40)


def test_notice_period_comes_from_the_clinic_file(tmp_path):
    clinic, clock, desk = setup(tmp_path, cancellation_notice_hours=2)
    first = desk.book("amy", MONDAY, time(9, 0), "Ann Lee", "07700900001")
    second = desk.book("amy", MONDAY, time(12, 20), "Bob Ray", "07700900002")
    clock.moment = datetime(2026, 3, 2, 8, 0)
    assert desk.cancel(first.id).status == "late_cancelled"
    assert desk.cancel(second.id).status == "cancelled"
