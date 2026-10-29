import csv
import json

from clinicbook.cli.main import main

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


def write_clinic(folder, **settings):
    (folder / "clinic.json").write_text(json.dumps(dict(CLINIC, settings=settings)), encoding="utf-8")


def cli(folder, *argv, now="2026-02-27T08:00"):
    return main(["--clinic", str(folder / "clinic.json"), "--bookings", str(folder / "bookings.csv"),
                 "--now", now, *argv])


def statuses(folder):
    with open(folder / "bookings.csv", newline="", encoding="utf-8") as handle:
        return {row["id"]: row["status"] for row in csv.DictReader(handle)}


def test_cancel_command_records_late_cancellations(tmp_path):
    write_clinic(tmp_path)
    assert cli(tmp_path, "book", "amy", "2026-03-02", "14:00", "--patient", "Ann Lee", "--phone", "07700900001") == 0
    assert cli(tmp_path, "book", "amy", "2026-03-05", "14:00", "--patient", "Bob Ray", "--phone", "07700900002") == 0
    assert cli(tmp_path, "cancel", "B0001", now="2026-03-02T09:00") == 0
    assert cli(tmp_path, "cancel", "B0002", now="2026-03-02T09:00") == 0
    assert statuses(tmp_path) == {"B0001": "late_cancelled", "B0002": "cancelled"}


def test_cancel_command_uses_the_clinic_files_notice_period(tmp_path):
    write_clinic(tmp_path, cancellation_notice_hours=1)
    assert cli(tmp_path, "book", "amy", "2026-03-02", "14:00", "--patient", "Ann Lee", "--phone", "07700900001") == 0
    assert cli(tmp_path, "book", "amy", "2026-03-02", "15:40", "--patient", "Bob Ray", "--phone", "07700900002") == 0
    assert cli(tmp_path, "cancel", "B0001", now="2026-03-02T12:00") == 0
    assert cli(tmp_path, "cancel", "B0002", now="2026-03-02T15:00") == 0
    assert statuses(tmp_path) == {"B0001": "cancelled", "B0002": "late_cancelled"}
