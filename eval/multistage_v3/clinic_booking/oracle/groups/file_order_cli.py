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


def file_ids(folder):
    with open(folder / "bookings.csv", newline="", encoding="utf-8") as handle:
        return [row["id"] for row in csv.DictReader(handle)]


def test_new_bookings_land_at_the_bottom(tmp_path):
    (tmp_path / "clinic.json").write_text(json.dumps(CLINIC), encoding="utf-8")
    assert cli(tmp_path, "book", "amy", "2026-03-06", "15:40", "--patient", "Ann Lee", "--phone", "07700900001") == 0
    assert cli(tmp_path, "book", "ben", "2026-03-02", "09:00", "--patient", "Bob Ray", "--phone", "07700900002") == 0
    assert file_ids(tmp_path) == ["B0001", "B0002"]
    assert cli(tmp_path, "book", "amy", "2026-03-02", "14:00", "--patient", "Cy Tan", "--phone", "07700900003") == 0
    assert cli(tmp_path, "book", "amy", "2026-03-02", "09:00", "--patient", "Dee Fox", "--phone", "07700900004") == 0
    assert file_ids(tmp_path) == ["B0001", "B0002", "B0003", "B0004"]
    assert cli(tmp_path, "cancel", "B0003") == 0
    assert file_ids(tmp_path) == ["B0001", "B0002", "B0003", "B0004"]
