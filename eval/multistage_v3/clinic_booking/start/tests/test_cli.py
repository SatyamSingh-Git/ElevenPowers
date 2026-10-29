import pytest

from clinicbook.cli.main import main
from clinicbook.storage.bookings_file import load_bookings


@pytest.fixture
def clinic_cli(clinic_file, tmp_path):
    bookings = tmp_path / "bookings.csv"

    def run(*argv, now="2026-02-27T08:00"):
        return main(["--clinic", str(clinic_file), "--bookings", str(bookings), "--now", now, *argv])

    run.bookings = bookings
    return run


def test_book_and_list(clinic_cli, capsys):
    assert clinic_cli("book", "amy", "2026-03-02", "09:00", "--patient", "Ann Lee", "--phone", "07700900001") == 0
    assert capsys.readouterr().out == "Booked B0001 for Ann Lee at 09:00 on 2026-03-02\n"
    assert clinic_cli("list", "monday") == 0
    assert "09:00  Amy Hart      R1    Ann Lee  Booked" in capsys.readouterr().out


def test_errors_go_to_stderr_with_exit_status_1(clinic_cli, capsys):
    assert clinic_cli("book", "amy", "2026-03-01", "09:00", "--patient", "Ann Lee", "--phone", "07700900001") == 1
    assert capsys.readouterr().err == "error: clinic is closed on 2026-03-01\n"


def test_cancel_saves_the_bookings(clinic_cli, capsys):
    clinic_cli("book", "ben", "2026-03-02", "10:40", "--patient", "Ann Lee", "--phone", "07700900001")
    assert clinic_cli("cancel", "B0001") == 0
    assert capsys.readouterr().out.endswith("Cancelled B0001\n")
    assert load_bookings(clinic_cli.bookings)[0].status == "cancelled"


def test_slots_lists_by_day(clinic_cli, capsys):
    assert clinic_cli("slots", "--from", "2026-03-07", "--days", "1", "--practitioner", "cara") == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0] == "Saturday 07 March"
    assert out[1] == "  09:00  Cara Diaz (R3)"


def test_no_slots_on_a_closed_day(clinic_cli, capsys):
    assert clinic_cli("slots", "--from", "2026-03-01", "--days", "1") == 0
    assert capsys.readouterr().out == "No free slots\nThe clinic next opens on Monday 02 March\n"
