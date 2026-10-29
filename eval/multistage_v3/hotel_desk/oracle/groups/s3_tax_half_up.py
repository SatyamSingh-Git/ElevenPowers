"""Stage 3: tax on each folio charge is rounded half up to the cent."""
from datetime import date, datetime
import json

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
        {"code": "KG", "name": "King", "max_adults": 2, "base_rate": "150.00"},
    ],
    "rooms": [{"number": "101", "type": "QN"}, {"number": "201", "type": "KG"}],
    "rate_plans": [{"code": "BAR", "name": "Best available"}],
}


def _in_house(room_type="KG"):
    hotel = build_hotel(SETUP, MONDAY)
    settings = Settings()
    reservation = booking.book(hotel, settings, guest="Ann Lee", room_type=room_type, arrival=MONDAY,
                               departure=date(2026, 3, 9))
    stays.check_in(hotel, FixedClock(datetime(2026, 3, 2, 15, 0)), reservation.id)
    return hotel, settings, reservation


def test_sales_tax_rounds_half_up():
    hotel, _, reservation = _in_house()
    assert [c.amount for c in billing.post_charge(hotel, reservation.id, "MB", 1250)] == [1250, 91]
    assert [c.amount for c in billing.post_charge(hotel, reservation.id, "FB", 1000)] == [1000, 73]
    assert [c.amount for c in billing.post_charge(hotel, reservation.id, "PK", 2000)] == [2000, 145]


def test_room_tax_rounds_half_up_at_the_night_audit():
    hotel, settings, reservation = _in_house()
    for _ in range(6):
        night_audit.run_audit(hotel, settings)
    taxes = [c.amount for c in hotel.folio(reservation.id).charges if c.code == "TAX"]
    # Monday to Thursday at 150.00, then Friday and Saturday at 165.00.
    assert taxes == [1763, 1763, 1763, 1763, 1939, 1939]


def test_cli_post_shows_rounded_tax(tmp_path, capsys):
    setup_file = tmp_path / "setup.json"
    setup_file.write_text(json.dumps(SETUP))
    state = str(tmp_path / "hotel-state.json")

    def run(*argv):
        return main(["--state", state, "--settings", str(tmp_path / "hotel.json"), *argv])

    run("init", str(setup_file), "--business-date", "2026-03-02")
    run("book", "--guest", "Ann Lee", "--type", "QN", "--arrival", "2026-03-02", "--departure", "2026-03-03")
    run("checkin", "R0001")
    capsys.readouterr()
    assert run("post", "R0001", "MB", "12.50") == 0
    assert "Posted TAX 0.91 to R0001" in capsys.readouterr().out
