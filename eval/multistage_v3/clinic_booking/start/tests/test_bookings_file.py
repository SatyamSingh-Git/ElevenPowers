import csv

import pytest

from clinicbook.errors import StorageError
from clinicbook.storage.bookings_file import COLUMNS, load_bookings, save_bookings
from clinicbook.storage.ids import booking_number, next_booking_id
from conftest import MONDAY, at


def test_round_trip(desk, tmp_path):
    desk.book("amy", MONDAY, at("09:00"), "Ann Lee", "07700900001")
    desk.cancel(desk.book("ben", MONDAY, at("10:40"), "Bob Ray", "07700900002").id)
    path = tmp_path / "bookings.csv"
    save_bookings(desk.bookings, path)
    assert load_bookings(path) == desk.bookings


def test_rows_are_written_by_day_and_start_time(desk, tmp_path):
    desk.book("amy", MONDAY, at("14:00"), "Ann Lee", "07700900001")
    desk.book("amy", MONDAY, at("09:00"), "Bob Ray", "07700900002")
    path = tmp_path / "bookings.csv"
    save_bookings(desk.bookings, path)
    with path.open(newline="", encoding="utf-8") as handle:
        assert [row["id"] for row in csv.DictReader(handle)] == ["B0002", "B0001"]


def test_missing_file_means_no_bookings(tmp_path):
    assert load_bookings(tmp_path / "bookings.csv") == []


def test_unknown_status_is_reported_with_its_line(tmp_path):
    path = tmp_path / "bookings.csv"
    path.write_text(",".join(COLUMNS) + "\n"
                    "B0001,Ann Lee,07700900001,amy,R1,2026-03-02,09:00,20,maybe,\n", encoding="utf-8")
    with pytest.raises(StorageError, match="bookings.csv:2: unknown status maybe"):
        load_bookings(path)


def test_wrong_columns_are_refused(tmp_path):
    path = tmp_path / "bookings.csv"
    path.write_text("id,patient\n", encoding="utf-8")
    with pytest.raises(StorageError, match="expected columns"):
        load_bookings(path)


def test_references_count_up_from_the_highest(desk):
    assert next_booking_id([]) == "B0001"
    desk.book("amy", MONDAY, at("09:00"), "Ann Lee", "07700900001")
    desk.bookings[0].id = "B0041"
    assert next_booking_id(desk.bookings) == "B0042"
    assert booking_number("B0042") == 42
