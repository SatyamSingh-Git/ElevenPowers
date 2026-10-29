"""The night audit end to end: the journal it keeps, the revenue read back from it, the audit report."""
from datetime import date, datetime
import json

from hoteldesk.cli import main
from hoteldesk.clock import FixedClock
from hoteldesk.config import Settings
from hoteldesk.reports.audit_report import audit_report_text
from hoteldesk.reports.revenue import revenue_summary
from hoteldesk.services import billing, booking, night_audit, stays
from hoteldesk.storage.setup import build_hotel

MONDAY = date(2026, 3, 2)
SETUP = {
    "name": "Harbour View Inn",
    "room_types": [
        {"code": "QN", "name": "Queen", "max_adults": 2, "base_rate": "120.00"},
        {"code": "KG", "name": "King", "max_adults": 2, "base_rate": "150.00"},
        {"code": "ST", "name": "Suite", "max_adults": 4, "base_rate": "260.00"},
    ],
    "rooms": [
        {"number": "101", "type": "QN"},
        {"number": "102", "type": "QN"},
        {"number": "201", "type": "KG"},
        {"number": "202", "type": "KG"},
        {"number": "301", "type": "ST"},
    ],
    "rate_plans": [{"code": "BAR", "name": "Best available"}],
}


def _two_guests():
    hotel = build_hotel(SETUP, MONDAY)
    settings = Settings()
    clock = FixedClock(datetime(2026, 3, 2, 16, 0))
    ann = booking.book(hotel, settings, guest="Ann Lee", room_type="QN", arrival=MONDAY, departure=date(2026, 3, 5))
    bo = booking.book(hotel, settings, guest="Bo Chen", room_type="ST", arrival=MONDAY, departure=date(2026, 3, 4))
    stays.check_in(hotel, clock, ann.id)
    stays.check_in(hotel, clock, bo.id)
    billing.post_charge(hotel, ann.id, "MB", 1200)
    return hotel, settings, clock, ann, bo


def _three_days(journal):
    """Bo leaves after two nights, settling his folio; Ann stays a third."""
    hotel, settings, clock, ann, bo = _two_guests()
    night_audit.run_audit(hotel, settings, journal)
    night_audit.run_audit(hotel, settings, journal)
    billing.post_payment(hotel, bo.id, hotel.folio(bo.id).balance, "card")
    clock.set(datetime(2026, 3, 4, 9, 45))
    stays.check_out(hotel, settings, clock, bo.id)
    night_audit.run_audit(hotel, settings, journal)
    return hotel


def test_revenue_summary_totals_the_audited_days(tmp_path):
    journal = tmp_path / "audit_journal.csv"
    _three_days(journal)
    summary = revenue_summary(journal)
    assert [day["date"] for day in summary["days"]] == [date(2026, 3, 2), date(2026, 3, 3), date(2026, 3, 4)]
    assert [day["room_revenue"] for day in summary["days"]] == [38000, 38000, 12000]
    totals = summary["totals"]
    assert totals["rooms_sold"] == 5
    assert totals["room_revenue"] == 88000
    assert totals["tax_revenue"] == 3 * 1410 + 2 * 3055 + 87
    assert totals["other_revenue"] == 1200
    assert totals["adr"] == 17600
    assert totals["payments"] == 2 * (26000 + 3055)


def test_revenue_summary_by_date_range(tmp_path):
    journal = tmp_path / "audit_journal.csv"
    _three_days(journal)
    summary = revenue_summary(journal, date(2026, 3, 3), date(2026, 3, 4))
    assert summary["totals"]["room_revenue"] == 50000
    assert summary["totals"]["rooms_sold"] == 3


def test_revenue_command_after_audits(tmp_path, capsys):
    setup_file = tmp_path / "setup.json"
    setup_file.write_text(json.dumps(SETUP))
    state = str(tmp_path / "hotel-state.json")
    settings_file = str(tmp_path / "hotel.json")

    def run(*argv):
        return main(["--state", state, "--settings", settings_file, *argv])

    assert run("init", str(setup_file), "--business-date", "2026-03-02") == 0
    assert run("book", "--guest", "Ann Lee", "--type", "QN", "--arrival", "2026-03-02",
               "--departure", "2026-03-04") == 0
    assert run("checkin", "R0001") == 0
    assert run("audit") == 0
    assert run("audit") == 0
    capsys.readouterr()
    assert run("revenue") == 0
    out = capsys.readouterr().out
    total = [line for line in out.splitlines() if line.startswith("total")]
    assert len(total) == 1 and "240.00" in total[0] and "28.20" in total[0]


def test_audit_report_shows_occupancy_and_revenue():
    hotel, settings, clock, ann, bo = _two_guests()
    result = night_audit.run_audit(hotel, settings)
    text = audit_report_text(hotel, result)
    assert "Night audit for 2026-03-02" in text
    assert "Rooms sold: 2 of 5" in text
    assert "Occupancy: 40.0%" in text
    assert "380.00" in text


def test_audit_command_prints_occupancy(tmp_path, capsys):
    setup_file = tmp_path / "setup.json"
    setup_file.write_text(json.dumps(SETUP))
    state = str(tmp_path / "hotel-state.json")
    settings_file = str(tmp_path / "hotel.json")

    def run(*argv):
        return main(["--state", state, "--settings", settings_file, *argv])

    run("init", str(setup_file), "--business-date", "2026-03-02")
    run("book", "--guest", "Ann Lee", "--type", "QN", "--arrival", "2026-03-02", "--departure", "2026-03-04")
    run("checkin", "R0001")
    run("hk", "202", "out_of_order")
    capsys.readouterr()
    assert run("audit") == 0
    assert "Occupancy: 25.0%" in capsys.readouterr().out
