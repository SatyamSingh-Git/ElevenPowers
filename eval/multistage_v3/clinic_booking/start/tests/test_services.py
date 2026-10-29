from datetime import date, datetime, timedelta

import pytest

from clinicbook.errors import BookingError
from clinicbook.services import waitlist
from clinicbook.services.checks import problems
from clinicbook.services.closures import stranded
from clinicbook.services.patients import directory, frequent_no_shows, search
from clinicbook.services.reminders import append_outbox, due_reminders, read_sent
from clinicbook.services.series import book_series
from clinicbook.storage.partner_import import import_partner_file
from clinicbook.storage.waitlist_file import load_waitlist, save_waitlist
from conftest import MONDAY, at


def test_reminders_are_due_within_the_lead_time(desk, clinic, tmp_path):
    desk.book("amy", MONDAY, at("09:00"), "Ann Lee", "07700900001")
    desk.book("amy", MONDAY + timedelta(days=1), at("09:00"), "Bob Ray", "07700900002")
    now = datetime(2026, 3, 1, 10, 0)
    due = due_reminders(desk.bookings, clinic, now)
    assert [reminder.booking for reminder in due] == ["B0001"]
    assert due[0].text == ("Ann, a reminder of your appointment with Amy Hart at 09:00 "
                           "on Monday 02 March. Reply C to cancel.")
    outbox = tmp_path / "outbox.csv"
    append_outbox(due, outbox)
    assert read_sent(outbox) == {"B0001"}
    assert due_reminders(desk.bookings, clinic, now, read_sent(outbox)) == []


def test_series_is_all_or_nothing(desk):
    later = date(2026, 3, 16)
    made = book_series(desk, "amy", later, at("09:00"), 3, "Ann Lee", "07700900001")
    assert [booking.day for booking in made] == [later + timedelta(weeks=n) for n in range(3)]
    with pytest.raises(BookingError, match=r"week 3 \(2026-03-16\): Amy Hart is already booked at 09:00"):
        book_series(desk, "amy", MONDAY, at("09:00"), 3, "Bob Ray", "07700900002")
    assert len(desk.bookings) == 3


def test_a_single_week_reports_the_plain_error(desk):
    with pytest.raises(BookingError) as caught:
        book_series(desk, "amy", date(2026, 3, 1), at("09:00"), 1, "Bob Ray", "07700900002")
    assert str(caught.value) == "clinic is closed on 2026-03-01"


def test_waiting_list_offers_longest_waiting_first(desk, clinic, tmp_path):
    now = datetime(2026, 2, 27, 8, 0)
    queue = []
    waitlist.add(queue, waitlist.new_entry(clinic, "Ann Lee", "07700900001", "cara", MONDAY,
                                           MONDAY + timedelta(days=2), now))
    waitlist.add(queue, waitlist.new_entry(clinic, "Bob Ray", "07700900002", "any", MONDAY,
                                           MONDAY, now + timedelta(minutes=5)))
    with pytest.raises(BookingError, match="already waiting"):
        waitlist.add(queue, waitlist.new_entry(clinic, "Ann Lee", "07700900001", "cara", MONDAY, MONDAY, now))
    path = tmp_path / "waitlist.json"
    save_waitlist(queue, path)
    assert load_waitlist(path) == queue
    offers = waitlist.offers(queue, clinic, desk.bookings, now)
    assert [(o.entry.patient, o.slot.practitioner, o.slot.day) for o in offers] == [
        ("Ann Lee", "cara", date(2026, 3, 3)),
        ("Bob Ray", "amy", MONDAY),
    ]


def test_partner_import_skips_bad_rows(desk, tmp_path):
    path = tmp_path / "partner.csv"
    path.write_text("Date,Time,Clinician,Client,Mobile\n"
                    "02/03/2026,9:00,amy hart,Ann Lee,07700900001\n"
                    "02/03/2026,9:00,Amy Hart,Bob Ray,07700900002\n"
                    "02/03/2026,9:00,Zed,Cy Tan,07700900003\n", encoding="utf-8")
    report = import_partner_file(path, desk)
    assert [booking.patient for booking in report.booked] == ["Ann Lee"]
    assert report.skipped == [(3, "Amy Hart is already booked at 09:00"), (4, "unknown clinician Zed")]


def test_checks_find_clashes_typed_into_the_file(desk, clinic):
    desk.book("amy", MONDAY, at("09:00"), "Ann Lee", "07700900001")
    desk.book("ben", MONDAY, at("09:00"), "Bob Ray", "07700900002")
    assert problems(desk.bookings, clinic) == []
    desk.bookings[1].room = "R1"
    assert problems(desk.bookings, clinic) == ["B0001 and B0002: room R1 booked twice at 09:00"]


def test_stranded_bookings_on_a_new_closure(desk, clinic):
    desk.book("amy", MONDAY, at("09:00"), "Ann Lee", "07700900001")
    clinic.hours.closures = frozenset({MONDAY})
    (found,) = stranded(desk.bookings, clinic, MONDAY, MONDAY)
    assert found[1] == "closed"


def test_patient_directory(desk, clock):
    desk.book("amy", MONDAY, at("09:00"), "Ann Lee", "07700900001")
    desk.book("amy", date(2026, 3, 3), at("09:00"), "Ann Lee-Smith", "07700900001")
    desk.book("ben", MONDAY, at("09:00"), "Bob Ray", "07700900002")
    clock.moment = datetime(2026, 3, 3, 18, 0)
    desk.mark_no_show("B0001")
    desk.mark_no_show("B0002")
    records = directory(desk.bookings)
    assert [(r.name, r.bookings, r.no_shows) for r in records] == [("Ann Lee-Smith", 2, 2), ("Bob Ray", 1, 0)]
    assert [r.name for r in search(records, "0770090000")] == ["Ann Lee-Smith", "Bob Ray"]
    assert [r.name for r in frequent_no_shows(records, 2)] == ["Ann Lee-Smith"]
