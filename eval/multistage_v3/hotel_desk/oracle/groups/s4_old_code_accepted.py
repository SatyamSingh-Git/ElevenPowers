"""Stage 4: ROOM can be posted, and the command line still takes the old code RM, recording it as ROOM."""
from datetime import date, datetime
import json

from hoteldesk.cli import main
from hoteldesk.clock import FixedClock
from hoteldesk.config import Settings
from hoteldesk.services import billing, booking, stays
from hoteldesk.storage.setup import build_hotel

MONDAY = date(2026, 3, 2)
SETUP = {
    "name": "Harbour View Inn",
    "room_types": [{"code": "QN", "name": "Queen", "max_adults": 2, "base_rate": "120.00"}],
    "rooms": [{"number": "101", "type": "QN"}],
    "rate_plans": [{"code": "BAR", "name": "Best available"}],
}


def test_api_posts_room():
    hotel = build_hotel(SETUP, MONDAY)
    settings = Settings()
    reservation = booking.book(hotel, settings, guest="Ann Lee", room_type="QN", arrival=MONDAY,
                               departure=date(2026, 3, 3))
    stays.check_in(hotel, FixedClock(datetime(2026, 3, 2, 15, 0)), reservation.id)
    posted = billing.post_charge(hotel, reservation.id, "ROOM", 4000, "Day use")
    assert [(c.code, c.amount) for c in posted] == [("ROOM", 4000), ("TAX", 470)]


def test_cli_post_accepts_rm(tmp_path, capsys):
    setup_file = tmp_path / "setup.json"
    setup_file.write_text(json.dumps(SETUP))
    state = str(tmp_path / "hotel-state.json")

    def run(*argv):
        return main(["--state", state, "--settings", str(tmp_path / "hotel.json"), *argv])

    run("init", str(setup_file), "--business-date", "2026-03-02")
    run("book", "--guest", "Ann Lee", "--type", "QN", "--arrival", "2026-03-02", "--departure", "2026-03-03")
    run("checkin", "R0001")
    capsys.readouterr()
    assert run("post", "R0001", "RM", "40.00") == 0
    assert run("post", "R0001", "room", "10.00") == 0
    out = capsys.readouterr().out
    assert "Posted ROOM 40.00 to R0001" in out
    assert "Posted ROOM 10.00 to R0001" in out
