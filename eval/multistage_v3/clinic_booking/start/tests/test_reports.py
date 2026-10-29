import csv
from datetime import date, datetime

from clinicbook.reports.calendar import calendar_lines
from clinicbook.reports.day_schedule import export_day, schedule_rows
from clinicbook.reports.practitioner_sheet import sheet_lines
from clinicbook.reports.summary import day_summary
from clinicbook.reports.textfmt import table
from clinicbook.reports.utilisation import RoomLoad
from clinicbook.reports.week import week_grid
from conftest import MONDAY, at


def test_export_writes_one_row_per_booking(desk, clinic, tmp_path):
    desk.book("amy", MONDAY, at("09:00"), "Ann Lee", "07700900001")
    desk.book("ben", MONDAY, at("10:40"), "Bob Ray", "07700900002")
    desk.book("amy", date(2026, 3, 3), at("09:00"), "Cy Tan", "07700900003")
    path = tmp_path / "day.csv"
    assert export_day(desk.bookings, clinic, MONDAY, path) == 2
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert rows == [
        ["date", "start", "end", "practitioner", "room", "patient", "phone", "status"],
        ["2026-03-02", "09:00", "09:20", "Amy Hart", "R1", "Ann Lee", "07700900001", "Booked"],
        ["2026-03-02", "10:40", "11:00", "Ben Okafor", "R2", "Bob Ray", "07700900002", "Booked"],
    ]


def test_schedule_rows_carry_the_practitioner_name(desk, clinic):
    desk.book("ben", MONDAY, at("09:00"), "Ann Lee", "07700900001")
    (row,) = schedule_rows(desk.bookings, clinic, MONDAY)
    assert (row.practitioner, row.status_text) == ("Ben Okafor", "Booked")


def test_room_load_percent():
    assert RoomLoad("R1", "Room 1", 120, 480).percent == 25
    assert RoomLoad("R1", "Room 1", 0, 0).percent == 0


def test_summary_counts_by_status(desk, clinic, clock):
    first = desk.book("amy", MONDAY, at("09:00"), "Ann Lee", "07700900001")
    desk.book("ben", MONDAY, at("09:00"), "Bob Ray", "07700900002")
    desk.cancel(desk.book("amy", MONDAY, at("10:40"), "Cy Tan", "07700900003").id)
    clock.moment = datetime(2026, 3, 2, 12, 0)
    desk.mark_attended(first.id)
    summary = day_summary(desk.bookings, clinic, MONDAY)
    assert summary.counts == {"attended": 1, "booked": 1, "cancelled": 1}
    assert summary.seen_by == {"Amy Hart": 1, "Ben Okafor": 1}
    assert summary.appointments == 3


def test_week_grid_marks_days_off(desk, clinic):
    desk.book("ben", MONDAY, at("09:00"), "Ann Lee", "07700900001")
    days, grid = week_grid(desk.bookings, clinic, date(2026, 3, 4))
    assert days[0] == MONDAY
    assert grid["ben"] == [1, None, 0, None, 0, None, None]


def test_practitioner_sheet_shows_gaps(desk, clinic):
    desk.book("amy", MONDAY, at("10:40"), "Ann Lee", "07700900001")
    lines = sheet_lines(desk.bookings, clinic, "amy", MONDAY)
    assert lines[1:] == [
        "09:00  (100 min free)",
        "10:40  Ann Lee  07700900001  [B0001]",
        "11:00  (360 min free)",
        "1 patients",
    ]


def test_calendar_leaves_out_phone_numbers(desk, clinic):
    desk.book("amy", MONDAY, at("09:00"), "Lee, Ann", "07700900001")
    lines = calendar_lines(desk.bookings, clinic, "amy", MONDAY, MONDAY)
    assert "DTSTART:20260302T090000" in lines
    assert "SUMMARY:Lee\\, Ann" in lines
    assert not any("07700900001" in line for line in lines)


def test_table_aligns_numbers_right():
    assert table(["name", "n"], [["a", 5], ["bb", 10]]) == ["name   n", "----  --", "a      5", "bb    10"]
