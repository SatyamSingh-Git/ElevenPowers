"""Stage 7: the night audit removes cancelled reservations past the retention period (30 days by default)."""
from datetime import date, datetime
import json

import pytest

from hoteldesk.cli import main
from hoteldesk.clock import FixedClock
from hoteldesk.config import Settings
from hoteldesk.errors import NotFound
from hoteldesk.services import billing, booking, night_audit, stays
from hoteldesk.storage.setup import build_hotel

MONDAY = date(2026, 3, 2)
SETUP = {
    "name": "Harbour View Inn",
    "room_types": [{"code": "QN", "name": "Queen", "max_adults": 2, "base_rate": "120.00"}],
    "rooms": [{"number": "101", "type": "QN"}, {"number": "102", "type": "QN"}],
    "rate_plans": [{"code": "BAR", "name": "Best available"}],
}


def _audit_until(hotel, settings, last_closed):
    while hotel.business_date <= last_closed:
        night_audit.run_audit(hotel, settings)


def test_cancellation_kept_30_days_after_departure_then_removed():
    hotel = build_hotel(SETUP, MONDAY)
    settings = Settings()
    assert settings.cancelled_retention_days == 30
    cancelled = booking.book(hotel, settings, guest="Ann Lee", room_type="QN", arrival=date(2026, 3, 3),
                             departure=date(2026, 3, 4))
    booking.cancel(hotel, cancelled.id)
    _audit_until(hotel, settings, date(2026, 4, 3))
    assert hotel.reservation(cancelled.id).status == "cancelled"
    _audit_until(hotel, settings, date(2026, 4, 4))
    with pytest.raises(NotFound):
        hotel.reservation(cancelled.id)


def test_only_cancellations_are_removed():
    hotel = build_hotel(SETUP, MONDAY)
    settings = Settings()
    clock = FixedClock(datetime(2026, 3, 2, 15, 0))
    stayed = booking.book(hotel, settings, guest="Ann Lee", room_type="QN", arrival=MONDAY,
                          departure=date(2026, 3, 3))
    missed = booking.book(hotel, settings, guest="Bo Chen", room_type="QN", arrival=MONDAY,
                          departure=date(2026, 3, 3))
    stays.check_in(hotel, clock, stayed.id)
    night_audit.run_audit(hotel, settings)
    billing.post_payment(hotel, stayed.id, hotel.folio(stayed.id).balance)
    clock.set(datetime(2026, 3, 3, 9, 0))
    stays.check_out(hotel, settings, clock, stayed.id)
    _audit_until(hotel, settings, date(2026, 5, 1))
    assert hotel.reservation(stayed.id).status == "checked_out"
    assert hotel.reservation(missed.id).status == "no_show"


def test_removed_reservation_is_gone_from_the_cli(tmp_path, capsys):
    setup_file = tmp_path / "setup.json"
    setup_file.write_text(json.dumps(SETUP))
    state = str(tmp_path / "hotel-state.json")

    def run(*argv):
        return main(["--state", state, "--settings", str(tmp_path / "hotel.json"), *argv])

    run("init", str(setup_file), "--business-date", "2026-03-02")
    run("book", "--guest", "Ann Lee", "--type", "QN", "--arrival", "2026-03-02", "--departure", "2026-03-03")
    run("cancel", "R0001")
    for _ in range(33):
        assert run("audit") == 0
    capsys.readouterr()
    assert run("show", "R0001") == 1
    assert capsys.readouterr().err == "error: No reservation R0001\n"
