"""Stage 6: report occupancy --format json gives a percentage; the text report still reads as one."""
import json

from hoteldesk.cli import main

SETUP = {
    "name": "Harbour View Inn",
    "room_types": [{"code": "QN", "name": "Queen", "max_adults": 2, "base_rate": "120.00"}],
    "rooms": [{"number": str(number), "type": "QN"} for number in range(101, 109)],
    "rate_plans": [{"code": "BAR", "name": "Best available"}],
}


def _desk(tmp_path):
    setup_file = tmp_path / "setup.json"
    setup_file.write_text(json.dumps(SETUP))
    state = str(tmp_path / "hotel-state.json")

    def run(*argv):
        return main(["--state", state, "--settings", str(tmp_path / "hotel.json"), *argv])

    run("init", str(setup_file), "--business-date", "2026-03-02")
    for guest in ("Ann Lee", "Bo Chen", "Cy Diaz"):
        run("book", "--guest", guest, "--type", "QN", "--arrival", "2026-03-02", "--departure", "2026-03-04")
    return run


def test_json_report_gives_a_percentage(tmp_path, capsys):
    run = _desk(tmp_path)
    capsys.readouterr()
    assert run("report", "occupancy", "--format", "json") == 0
    rows = json.loads(capsys.readouterr().out)
    assert [row["occupancy"] for row in rows[:3]] == [37.5, 37.5, 0.0]


def test_text_report_shows_percent(tmp_path, capsys):
    run = _desk(tmp_path)
    capsys.readouterr()
    assert run("report", "occupancy") == 0
    out = capsys.readouterr().out
    assert "37.5%" in out
    assert "3750" not in out
