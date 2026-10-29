import json
from datetime import date, datetime, time
from decimal import Decimal

from clinicbook.cli.main import main
from clinicbook.clock import FixedClock
from clinicbook.services.desk import Desk
from clinicbook.services.fees import charges
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


def test_first_no_show_is_free_and_later_ones_are_charged(tmp_path):
    path = tmp_path / "clinic.json"
    path.write_text(json.dumps(CLINIC), encoding="utf-8")
    clinic = load_clinic(path)
    clock = FixedClock(datetime(2026, 2, 27, 8, 0))
    desk = Desk(clinic, [], clock)
    later = desk.book("amy", date(2026, 3, 6), time(9, 0), "Ann Lee", "07700900001")
    earliest = desk.book("amy", date(2026, 3, 2), time(9, 0), "Ann Lee", "07700900001")
    middle = desk.book("ben", date(2026, 3, 4), time(9, 0), "Ann Lee", "07700900001")
    once = desk.book("ben", date(2026, 3, 2), time(9, 0), "Bob Ray", "07700900002")
    came = desk.book("amy", date(2026, 3, 3), time(9, 0), "Cy Tan", "07700900003")
    clock.moment = datetime(2026, 3, 6, 18, 0)
    for booking in (later, earliest, middle, once):
        desk.mark_no_show(booking.id)
    desk.mark_attended(came.id)
    owed = charges(desk.bookings, clinic.settings)
    charged = {charge.booking: charge.amount for charge in owed if charge.amount}
    assert charged == {middle.id: Decimal("25.00"), later.id: Decimal("25.00")}


def test_fees_command_leaves_out_the_first_no_show(tmp_path, capsys):
    (tmp_path / "clinic.json").write_text(json.dumps(CLINIC), encoding="utf-8")

    def cli(*argv, now="2026-02-27T08:00"):
        return main(["--clinic", str(tmp_path / "clinic.json"), "--bookings", str(tmp_path / "bookings.csv"),
                     "--now", now, *argv])

    assert cli("book", "amy", "2026-03-02", "09:00", "--patient", "Ann Lee", "--phone", "07700900001") == 0
    assert cli("book", "amy", "2026-03-03", "09:00", "--patient", "Ann Lee", "--phone", "07700900001") == 0
    for reference in ("B0001", "B0002"):
        assert cli("no-show", reference, now="2026-03-03T18:00") == 0
    capsys.readouterr()
    assert cli("fees") == 0
    out = capsys.readouterr().out
    assert "Total: £25.00" in out.splitlines()
