"""Stage 5: the command line prints the not-ready message with the room's status."""
import json

from hoteldesk.cli import main

SETUP = {
    "name": "Harbour View Inn",
    "room_types": [{"code": "QN", "name": "Queen", "max_adults": 2, "base_rate": "120.00"}],
    "rooms": [{"number": "101", "type": "QN"}, {"number": "102", "type": "QN"}],
    "rate_plans": [{"code": "BAR", "name": "Best available"}],
}


def test_checkin_to_a_dirty_room(tmp_path, capsys):
    setup_file = tmp_path / "setup.json"
    setup_file.write_text(json.dumps(SETUP))
    state = str(tmp_path / "hotel-state.json")

    def run(*argv):
        return main(["--state", state, "--settings", str(tmp_path / "hotel.json"), *argv])

    run("init", str(setup_file), "--business-date", "2026-03-02")
    run("book", "--guest", "Ann Lee", "--type", "QN", "--arrival", "2026-03-02", "--departure", "2026-03-03")
    run("hk", "102", "dirty")
    capsys.readouterr()
    assert run("checkin", "R0001", "--room", "102") == 1
    assert capsys.readouterr().err == "error: Room 102 is not ready: dirty\n"
    assert run("checkin", "R0001", "--room", "101") == 0
