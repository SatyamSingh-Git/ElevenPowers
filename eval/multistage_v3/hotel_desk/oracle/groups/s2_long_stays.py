"""Stage 2: stays of up to 45 nights by default."""
from datetime import date, timedelta
import json

import pytest

from hoteldesk.cli import main
from hoteldesk.config import Settings, load_settings
from hoteldesk.errors import HotelError
from hoteldesk.services import booking, pricing
from hoteldesk.storage.setup import build_hotel

MONDAY = date(2026, 3, 2)
SETUP = {
    "name": "Harbour View Inn",
    "room_types": [{"code": "QN", "name": "Queen", "max_adults": 2, "base_rate": "120.00"}],
    "rooms": [{"number": "101", "type": "QN"}, {"number": "102", "type": "QN"}],
    "rate_plans": [{"code": "BAR", "name": "Best available"}],
}


def test_default_is_45_nights(tmp_path):
    assert Settings().max_stay_nights == 45
    assert load_settings(tmp_path / "no-such-file.json").max_stay_nights == 45


def test_45_nights_book_and_quote():
    hotel = build_hotel(SETUP, MONDAY)
    settings = Settings()
    departure = MONDAY + timedelta(days=45)
    assert len(pricing.quote(hotel, settings, "QN", "BAR", MONDAY, departure).rates) == 45
    reservation = booking.book(hotel, settings, guest="Ann Lee", room_type="QN", arrival=MONDAY,
                               departure=departure)
    assert reservation.nights == 45


def test_46_nights_refused():
    hotel = build_hotel(SETUP, MONDAY)
    with pytest.raises(HotelError, match="^Stays are limited to 45 nights$"):
        booking.book(hotel, Settings(), guest="Ann Lee", room_type="QN", arrival=MONDAY,
                     departure=MONDAY + timedelta(days=46))


def test_cli_books_six_weeks(tmp_path, capsys):
    setup_file = tmp_path / "setup.json"
    setup_file.write_text(json.dumps(SETUP))
    state = str(tmp_path / "hotel-state.json")

    def run(*argv):
        return main(["--state", state, "--settings", str(tmp_path / "hotel.json"), *argv])

    run("init", str(setup_file), "--business-date", "2026-03-02")
    assert run("book", "--guest", "Ann Lee", "--type", "QN", "--arrival", "2026-03-02",
               "--departure", "2026-04-13") == 0
    assert "(42 nights)" in capsys.readouterr().out
    assert run("book", "--guest", "Bo Chen", "--type", "QN", "--arrival", "2026-03-02",
               "--departure", "2026-04-17") == 1
    assert "error: Stays are limited to 45 nights" in capsys.readouterr().err
