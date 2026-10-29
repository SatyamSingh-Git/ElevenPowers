import json
from datetime import date, datetime, time

import pytest

from clinicbook.cli.main import main
from clinicbook.clock import FixedClock
from clinicbook.errors import ClinicError
from clinicbook.services.desk import Desk
from clinicbook.storage.clinic_file import load_clinic

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


def write_clinic(folder):
    path = folder / "clinic.json"
    path.write_text(json.dumps(CLINIC), encoding="utf-8")
    return path


def test_desk_error_shows_what_was_typed(tmp_path):
    desk = Desk(load_clinic(write_clinic(tmp_path)), [], FixedClock(datetime(2026, 2, 27, 8, 0)))
    with pytest.raises(ClinicError) as caught:
        desk.book("amy", date(2026, 3, 2), time(9, 0), "Ann Lee", "12345")
    assert str(caught.value) == "invalid phone number: 12345"
    assert desk.bookings == []


def test_book_command_error_shows_what_was_typed(tmp_path, capsys):
    write_clinic(tmp_path)
    argv = ["--clinic", str(tmp_path / "clinic.json"), "--bookings", str(tmp_path / "bookings.csv"),
            "--now", "2026-02-27T08:00", "book", "amy", "2026-03-02", "09:00",
            "--patient", "Ann Lee", "--phone", "0770090012"]
    assert main(argv) == 1
    assert capsys.readouterr().err == "error: invalid phone number: 0770090012\n"
