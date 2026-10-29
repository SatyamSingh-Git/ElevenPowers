import json
from datetime import date, datetime, time
from decimal import Decimal

from clinicbook.cli.main import main
from clinicbook.clock import FixedClock
from clinicbook.reports.statement import statement_from_file
from clinicbook.reports.summary import day_summary
from clinicbook.services.availability import free_slots
from clinicbook.services.desk import Desk
from clinicbook.services.fees import charges, write_charges
from clinicbook.storage.bookings_file import load_bookings
from clinicbook.storage.clinic_file import load_clinic

MONDAY = date(2026, 3, 2)
WEDNESDAY = date(2026, 3, 4)
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


def starts(clinic, bookings, day, now, practitioner):
    return [slot.start for slot in free_slots(clinic, bookings, day, now, practitioner=practitioner)]


def no_show_days(folder):
    clinic = load_clinic(write_clinic(folder))
    clock = FixedClock(START)
    desk = Desk(clinic, [], clock)
    first = desk.book("amy", MONDAY, at("09:00"), "Ann Lee", "07700900001")
    other = desk.book("ben", MONDAY, at("09:00"), "Bob Ray", "07700900002")
    came = desk.book("amy", MONDAY, at("10:40"), "Cy Tan", "07700900003")
    second = desk.book("amy", WEDNESDAY, at("09:00"), "Ann Lee", "07700900001")
    clock.moment = datetime(2026, 3, 4, 18, 0)
    desk.mark_no_show(first.id)
    desk.mark_no_show(other.id)
    desk.mark_attended(came.id)
    desk.mark_no_show(second.id)
    return clinic, desk


def test_every_offered_slot_can_be_booked(tmp_path):
    clinic = load_clinic(write_clinic(tmp_path))
    desk = Desk(clinic, [], FixedClock(START))
    for practitioner in ("amy", "ben"):
        offered = free_slots(clinic, [], MONDAY, START, practitioner=practitioner)
        assert len(offered) > 10
        for n, slot in enumerate(offered):
            booking = desk.book(practitioner, slot.day, slot.start, f"Patient {n}", f"07{len(desk.bookings):09d}")
            assert booking.start == slot.start
        assert free_slots(clinic, desk.bookings, MONDAY, START, practitioner=practitioner) == []


def test_cancelled_slot_is_offered_again(tmp_path):
    clinic = load_clinic(write_clinic(tmp_path))
    desk = Desk(clinic, [], FixedClock(START))
    slot = free_slots(clinic, [], WEDNESDAY, START, practitioner="ben")[3]
    booking = desk.book("ben", slot.day, slot.start, "Ann Lee", "07700900001")
    assert slot.start not in starts(clinic, desk.bookings, WEDNESDAY, START, "ben")
    desk.cancel(booking.id)
    assert slot.start in starts(clinic, desk.bookings, WEDNESDAY, START, "ben")
    assert desk.book("ben", slot.day, slot.start, "Bob Ray", "07700900002").start == slot.start


def test_statement_matches_the_charges_it_was_written_from(tmp_path):
    clinic, desk = no_show_days(tmp_path)
    owed = charges(desk.bookings, clinic.settings)
    path = tmp_path / "charges.csv"
    write_charges(owed, path)
    for phone in ("07700900001", "07700900002"):
        theirs = [charge for charge in owed if charge.phone == phone]
        statement = statement_from_file(path, phone)
        assert statement.total == sum((charge.amount for charge in theirs), Decimal("0"))
        assert [line.booking for line in statement.lines] == [charge.booking for charge in theirs]
        assert [line.amount for line in statement.lines] == [charge.amount for charge in theirs]
    assert statement_from_file(path, "07700900001").total > 0


def test_statement_command_reads_what_fees_wrote(tmp_path, capsys):
    write_clinic(tmp_path)
    assert cli(tmp_path, "book", "amy", "2026-03-02", "09:00", "--patient", "Ann Lee", "--phone", "07700900001") == 0
    assert cli(tmp_path, "book", "amy", "2026-03-04", "09:00", "--patient", "Ann Lee", "--phone", "07700900001") == 0
    assert cli(tmp_path, "book", "ben", "2026-03-02", "09:00", "--patient", "Bob Ray", "--phone", "07700900002") == 0
    for reference in ("B0001", "B0002", "B0003"):
        assert cli(tmp_path, "no-show", reference, now="2026-03-04T18:00") == 0
    assert cli(tmp_path, "fees", "--out", str(tmp_path / "charges.csv")) == 0
    capsys.readouterr()
    assert cli(tmp_path, "statement", "07700900001", "--charges", str(tmp_path / "charges.csv")) == 0
    out = capsys.readouterr().out
    clinic = load_clinic(tmp_path / "clinic.json")
    owed = charges(load_bookings(tmp_path / "bookings.csv"), clinic.settings)
    expected = sum((charge.amount for charge in owed if charge.phone == "07700900001"), Decimal("0"))
    assert expected > 0
    assert f"Total: {clinic.settings.money(expected)}" in out


def test_summary_fees_match_the_charges_for_that_day(tmp_path):
    clinic, desk = no_show_days(tmp_path)
    owed = charges(desk.bookings, clinic.settings)
    for day in (MONDAY, WEDNESDAY):
        summary = day_summary(desk.bookings, clinic, day)
        assert summary.fees_due == sum((charge.amount for charge in owed if charge.day == day), Decimal("0"))


def test_summary_command_fees_match_the_fees_command(tmp_path, capsys):
    write_clinic(tmp_path)
    cli(tmp_path, "book", "amy", "2026-03-02", "09:00", "--patient", "Ann Lee", "--phone", "07700900001")
    cli(tmp_path, "book", "ben", "2026-03-02", "09:00", "--patient", "Bob Ray", "--phone", "07700900002")
    cli(tmp_path, "book", "amy", "2026-03-02", "10:40", "--patient", "Cy Tan", "--phone", "07700900003")
    for reference in ("B0001", "B0002"):
        assert cli(tmp_path, "no-show", reference, now="2026-03-02T18:00") == 0
    assert cli(tmp_path, "attend", "B0003", now="2026-03-02T18:00") == 0
    capsys.readouterr()
    assert cli(tmp_path, "summary", "2026-03-02") == 0
    out = capsys.readouterr().out
    clinic = load_clinic(tmp_path / "clinic.json")
    owed = charges(load_bookings(tmp_path / "bookings.csv"), clinic.settings)
    expected = sum((charge.amount for charge in owed if charge.day == MONDAY), Decimal("0"))
    assert f"Fees due: {clinic.settings.money(expected)}" in out
