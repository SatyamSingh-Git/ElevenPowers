import json

import pytest

from hoteldesk.cli import main

from conftest import SETUP


@pytest.fixture
def desk(tmp_path):
    setup_file = tmp_path / "setup.json"
    setup_file.write_text(json.dumps(SETUP))
    state = tmp_path / "hotel-state.json"
    assert main(["--state", str(state), "init", str(setup_file), "--business-date", "2026-03-02"]) == 0

    def run(*argv):
        return main(["--state", str(state), "--settings", str(tmp_path / "hotel.json"), *argv])

    return run


def test_book_and_check_in(desk, capsys):
    assert desk("book", "--guest", "Ann Lee", "--type", "QN", "--arrival", "2026-03-02",
                "--departure", "2026-03-04") == 0
    assert desk("checkin", "R0001") == 0
    out = capsys.readouterr().out
    assert "Booked R0001: Ann Lee, QN, 2026-03-02 to 2026-03-04 (2 nights), 240.00" in out
    assert "R0001 checked in to room 101" in out


def test_errors_are_printed(desk, capsys):
    assert desk("cancel", "R0042") == 1
    assert capsys.readouterr().err == "error: No reservation R0042\n"


def test_init_will_not_overwrite(tmp_path, desk, capsys):
    assert main(["--state", str(tmp_path / "hotel-state.json"), "init", "x.json", "--business-date",
                 "2026-03-02"]) == 1
    assert "already exists" in capsys.readouterr().err


def test_post_and_pay(desk, capsys):
    desk("book", "--guest", "Ann Lee", "--type", "QN", "--arrival", "2026-03-02", "--departure", "2026-03-03")
    desk("checkin", "R0001")
    assert desk("post", "R0001", "fb", "10.00") == 0
    assert desk("pay", "R0001", "10.00") == 0
    out = capsys.readouterr().out
    assert "Posted FB 10.00 to R0001" in out and "Posted TAX 0.72 to R0001" in out
    assert "Paid 10.00 by card; balance 0.72" in out


def test_audit_command(desk, capsys):
    desk("book", "--guest", "Ann Lee", "--type", "QN", "--arrival", "2026-03-02", "--departure", "2026-03-03")
    desk("checkin", "R0001")
    assert desk("audit") == 0
    assert "Night audit for 2026-03-02" in capsys.readouterr().out
    assert desk("report", "arrivals") == 0
    assert "Arrivals 2026-03-03: none" in capsys.readouterr().out


def test_settings_command(desk, capsys):
    assert desk("settings") == 0
    out = capsys.readouterr().out
    assert "check_out_time: 11:00" in out and "late_checkout_fee: 25.00" in out
