from datetime import date
import json

from hoteldesk.reports import folio_print
from hoteldesk.reports.registry import render_report
from hoteldesk.services import billing, booking, guests, stays

MONDAY = date(2026, 3, 2)


def test_arrivals(hotel, settings):
    booking.book(hotel, settings, guest="Bo Chen", room_type="KG", arrival=MONDAY, departure=date(2026, 3, 3),
                 rate_plan="AAA")
    guests.save_profile(hotel, "Bo Chen", vip=True)
    rows = json.loads(render_report("arrivals", hotel, MONDAY, "json"))
    assert rows == [{"reservation": "R0001", "guest": "Bo Chen", "vip": "yes", "type": "KG", "nights": 1,
                     "adults": 1, "plan": "AAA", "breakfast": "yes"}]


def test_empty_report(hotel):
    assert render_report("departures", hotel, MONDAY) == "Departures 2026-03-02: none"


def test_housekeeping_board_csv(hotel):
    lines = render_report("housekeeping", hotel, MONDAY, "csv").splitlines()
    assert lines[0] == "room,floor,type,status,occupied,task"
    assert lines[1] == "101,1,QN,clean,no,inspect"


def test_availability(hotel, settings):
    booking.book(hotel, settings, guest="Bo Chen", room_type="KG", arrival=MONDAY, departure=date(2026, 3, 3))
    rows = json.loads(render_report("availability", hotel, MONDAY, "json"))
    assert {"date": "2026-03-02", "type": "KG", "free": 1} in rows
    assert {"date": "2026-03-03", "type": "KG", "free": 2} in rows


def test_folio_print_lists_extras_and_payments(hotel, settings, clock):
    reservation = booking.book(hotel, settings, guest="Ann Lee", room_type="QN", arrival=MONDAY,
                               departure=date(2026, 3, 4))
    stays.check_in(hotel, clock, reservation.id)
    billing.post_charge(hotel, reservation.id, "PH", 450)
    billing.post_payment(hotel, reservation.id, 450, "cash")
    text = folio_print.print_folio(hotel, reservation.id)
    assert text.splitlines()[:2] == ["Harbour View Inn", "Folio R0001 - Ann Lee"]
    assert "Extras" in text and "Telephone" in text
    assert text.splitlines()[-1].startswith("Balance") and text.endswith("0.00")


def test_payments_report(hotel, settings, clock):
    reservation = booking.book(hotel, settings, guest="Ann Lee", room_type="QN", arrival=MONDAY,
                               departure=date(2026, 3, 4))
    stays.check_in(hotel, clock, reservation.id)
    billing.post_charge(hotel, reservation.id, "PH", 450)
    billing.post_payment(hotel, reservation.id, 450, "cash")
    assert json.loads(render_report("payments", hotel, MONDAY, "json")) == [
        {"reservation": "R0001", "guest": "Ann Lee", "method": "cash", "amount": "4.50"}]
