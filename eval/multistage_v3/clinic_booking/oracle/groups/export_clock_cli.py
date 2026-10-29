import csv
import json

from clinicbook.cli.main import main

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


def cli(folder, *argv, now="2026-02-27T08:00"):
    return main(["--clinic", str(folder / "clinic.json"), "--bookings", str(folder / "bookings.csv"),
                 "--now", now, *argv])


def test_schedule_command_writes_twelve_hour_times(tmp_path):
    (tmp_path / "clinic.json").write_text(json.dumps(CLINIC), encoding="utf-8")
    assert cli(tmp_path, "book", "ben", "2026-03-02", "10:40", "--patient", "Ann Lee", "--phone", "07700900001") == 0
    assert cli(tmp_path, "book", "amy", "2026-03-02", "15:40", "--patient", "Bob Ray", "--phone", "07700900002") == 0
    export = tmp_path / "day.csv"
    assert cli(tmp_path, "schedule", "2026-03-02", "--out", str(export)) == 0
    with open(export, newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == ["date", "start", "end", "practitioner", "room", "patient", "phone", "status"]
    assert [(row[1], row[2], row[5]) for row in rows[1:]] == [
        ("10:40 AM", "11:00 AM", "Ann Lee"),
        ("03:40 PM", "04:00 PM", "Bob Ray"),
    ]
