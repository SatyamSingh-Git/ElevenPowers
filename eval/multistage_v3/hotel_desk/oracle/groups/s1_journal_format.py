"""Stage 1: the audit journal writes its money columns as 0.00."""
import csv
from datetime import date, datetime
import json
import re

from hoteldesk.cli import main
from hoteldesk.clock import FixedClock
from hoteldesk.config import Settings
from hoteldesk.services import billing, booking, night_audit, stays
from hoteldesk.storage.setup import build_hotel

MONDAY = date(2026, 3, 2)
SETUP = {
    "name": "Harbour View Inn",
    "room_types": [
        {"code": "QN", "name": "Queen", "max_adults": 2, "base_rate": "120.00"},
        {"code": "ST", "name": "Suite", "max_adults": 4, "base_rate": "260.00"},
    ],
    "rooms": [{"number": "101", "type": "QN"}, {"number": "102", "type": "QN"}, {"number": "301", "type": "ST"}],
    "rate_plans": [{"code": "BAR", "name": "Best available"}],
}
MONEY = ("room_revenue", "tax_revenue", "other_revenue", "payments")


def _rows(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_journal_amounts_are_written_as_money(tmp_path):
    hotel = build_hotel(SETUP, MONDAY)
    settings = Settings()
    clock = FixedClock(datetime(2026, 3, 2, 16, 0))
    reservation = booking.book(hotel, settings, guest="Ann Lee", room_type="QN", arrival=MONDAY,
                               departure=date(2026, 3, 4))
    stays.check_in(hotel, clock, reservation.id)
    billing.post_charge(hotel, reservation.id, "PH", 350)
    journal = tmp_path / "audit_journal.csv"
    night_audit.run_audit(hotel, settings, journal)
    billing.post_payment(hotel, reservation.id, 10000, "cash")
    night_audit.run_audit(hotel, settings, journal)
    rows = _rows(journal)
    assert [(row["business_date"], row["rooms_sold"], row["rooms_available"]) for row in rows] == [
        ("2026-03-02", "1", "3"), ("2026-03-03", "1", "3")]
    assert [tuple(row[name] for name in MONEY) for row in rows] == [
        ("120.00", "14.10", "3.50", "0.00"),
        ("120.00", "14.10", "0.00", "100.00"),
    ]
    for row in rows:
        for name in MONEY:
            assert re.fullmatch(r"\d+\.\d\d", row[name])


def test_journal_columns_are_unchanged(tmp_path):
    hotel = build_hotel(SETUP, MONDAY)
    journal = tmp_path / "audit_journal.csv"
    night_audit.run_audit(hotel, Settings(), journal)
    header = journal.read_text(encoding="utf-8").splitlines()[0]
    assert header == "business_date,rooms_sold,rooms_available,room_revenue,tax_revenue,other_revenue,payments"
    assert tuple(_rows(journal)[0][name] for name in MONEY) == ("0.00", "0.00", "0.00", "0.00")


def test_cli_audit_writes_money_to_the_journal(tmp_path):
    setup_file = tmp_path / "setup.json"
    setup_file.write_text(json.dumps(SETUP))
    state = str(tmp_path / "hotel-state.json")

    def run(*argv):
        return main(["--state", state, "--settings", str(tmp_path / "hotel.json"), *argv])

    run("init", str(setup_file), "--business-date", "2026-03-02")
    run("book", "--guest", "Bo Chen", "--type", "ST", "--arrival", "2026-03-02", "--departure", "2026-03-03")
    run("checkin", "R0001")
    assert run("audit") == 0
    row = _rows(tmp_path / "audit_journal.csv")[0]
    assert (row["room_revenue"], row["tax_revenue"]) == ("260.00", "30.55")
