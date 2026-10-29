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


def write_clinic(folder, **settings):
    (folder / "clinic.json").write_text(json.dumps(dict(CLINIC, settings=settings)), encoding="utf-8")


def cli(folder, *argv, now="2026-02-27T08:00"):
    return main(["--clinic", str(folder / "clinic.json"), "--bookings", str(folder / "bookings.csv"),
                 "--now", now, *argv])


def book(folder, practitioner, start, phone="07700900001"):
    return cli(folder, "book", practitioner, "2026-03-02", start, "--patient", "Ann Lee", "--phone", phone)


def test_limit_of_one_from_the_clinic_file(tmp_path, capsys):
    write_clinic(tmp_path, max_daily_bookings=1)
    assert book(tmp_path, "amy", "09:00") == 0
    capsys.readouterr()
    assert book(tmp_path, "ben", "10:40") == 1
    assert capsys.readouterr().err.startswith("error: Ann Lee already has 1 booking")
    assert book(tmp_path, "ben", "10:40", phone="07700900002") == 0


def test_limit_of_three_from_the_clinic_file(tmp_path):
    write_clinic(tmp_path, max_daily_bookings=3)
    assert book(tmp_path, "amy", "09:00") == 0
    assert book(tmp_path, "ben", "10:40") == 0
    assert book(tmp_path, "amy", "14:00") == 0
    assert book(tmp_path, "ben", "15:40") == 1
