from datetime import date
import csv

from hoteldesk.reports.audit_report import audit_report_text
from hoteldesk.services import billing, booking, night_audit, stays

MONDAY = date(2026, 3, 2)


def test_audit_posts_room_and_tax_and_rolls_the_date(hotel, settings, clock):
    reservation = booking.book(hotel, settings, guest="Ann Lee", room_type="QN", arrival=MONDAY,
                               departure=date(2026, 3, 4))
    stays.check_in(hotel, clock, reservation.id)
    result = night_audit.run_audit(hotel, settings)
    charges = hotel.folio(reservation.id).charges
    assert [(c.day, c.amount) for c in charges] == [(MONDAY, 12000), (MONDAY, 1410)]
    assert charges[0].description == "Room 101 night of 2026-03-02"
    assert result.room_revenue == 12000 and result.tax_revenue == 1410
    assert hotel.business_date == date(2026, 3, 3)


def test_no_shows(hotel, settings):
    reservation = booking.book(hotel, settings, guest="Bo Chen", room_type="KG", arrival=MONDAY,
                               departure=date(2026, 3, 3))
    result = night_audit.run_audit(hotel, settings)
    assert result.no_shows == [reservation.id]
    assert reservation.status == "no_show"


def test_guest_past_departure_is_extended(hotel, settings, clock):
    reservation = booking.book(hotel, settings, guest="Ann Lee", room_type="QN", arrival=MONDAY,
                               departure=date(2026, 3, 3))
    stays.check_in(hotel, clock, reservation.id)
    night_audit.run_audit(hotel, settings)
    result = night_audit.run_audit(hotel, settings)
    assert result.extended == [reservation.id]
    assert reservation.departure == date(2026, 3, 4)
    assert len(reservation.rates) == 2


def test_audit_writes_one_journal_line_per_day(hotel, settings, clock, tmp_path):
    journal = tmp_path / "audit_journal.csv"
    night_audit.run_audit(hotel, settings, journal)
    night_audit.run_audit(hotel, settings, journal)
    with journal.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["business_date"] for row in rows] == ["2026-03-02", "2026-03-03"]


def test_audit_report_lists_revenue(hotel, settings, clock):
    reservation = booking.book(hotel, settings, guest="Ann Lee", room_type="QN", arrival=MONDAY,
                               departure=date(2026, 3, 4))
    stays.check_in(hotel, clock, reservation.id)
    billing.post_charge(hotel, reservation.id, "PH", 500)
    text = audit_report_text(hotel, night_audit.run_audit(hotel, settings))
    assert "Night audit for 2026-03-02" in text
    assert "Room revenue" in text and "120.00" in text
    assert "Other revenue" in text and "5.00" in text


def test_open_items(hotel, settings, clock):
    booking.book(hotel, settings, guest="Bo Chen", room_type="KG", arrival=MONDAY, departure=date(2026, 3, 3))
    assert night_audit.open_items(hotel) == ["R0001 Bo Chen has not arrived and will be a no-show"]
