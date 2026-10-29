from decimal import Decimal

import pytest

from helpers import entry, hourly, write_employees
from payroll.errors import ImportRejected, PayrollError
from payroll.services.timesheets import add_entry, blank_sheet, import_timesheet, remove_entries
from payroll.storage.timesheet_store import read_timesheet, write_timesheet


@pytest.fixture
def staffed(data):
    write_employees(data, hourly("E001"), hourly("E002"))
    return data


def upload(tmp_path, text):
    path = tmp_path / "upload.csv"
    path.write_text(text, encoding="utf-8")
    return path


def test_import_stores_the_rows(staffed, settings, tmp_path):
    path = upload(tmp_path, "employee_id,date,hours\nE001,2026-01-05,7.5\nE001,2026-01-06,8\n")
    import_timesheet(staffed, settings, "2026-W01", path)
    rows = read_timesheet(staffed, "2026-W01")
    assert [(row.day.isoformat(), row.hours, row.kind) for row in rows] == [
        ("2026-01-05", Decimal("7.50"), "work"), ("2026-01-06", Decimal("8.00"), "work")]


def test_import_reports_every_bad_row_and_keeps_nothing(staffed, settings, tmp_path):
    path = upload(tmp_path, "\n".join([
        "employee_id,date,hours,kind",
        "E009,2026-01-05,8,work",
        "E001,2026-01-12,8,work",
        "E001,2026-01-06,25,work",
        "E001,2026-01-07,8,holiday",
        "E001,7 Jan,8,work",
        "E002,2026-01-05,8,work",
        "E002,2026-01-05,2,work",
    ]) + "\n")
    with pytest.raises(ImportRejected) as rejected:
        import_timesheet(staffed, settings, "2026-W01", path)
    assert rejected.value.problems == [
        "line 2: unknown employee E009",
        "line 3: 2026-01-12 is outside period 2026-W01",
        "line 4: hours must be more than 0 and at most 24",
        "line 5: unknown kind holiday",
        "line 6: bad date 7 Jan",
        "line 8: duplicate row for E002 on 2026-01-05",
    ]
    assert read_timesheet(staffed, "2026-W01") == []


def test_missing_column(staffed, settings, tmp_path):
    with pytest.raises(PayrollError, match="missing column hours"):
        import_timesheet(staffed, settings, "2026-W01", upload(tmp_path, "employee_id,date\n"))


def test_rows_without_hours_are_skipped(staffed, settings, tmp_path):
    path = upload(tmp_path, "employee_id,date,hours,kind\nE001,2026-01-05,,\nE001,2026-01-06,8,\n")
    assert len(import_timesheet(staffed, settings, "2026-W01", path)) == 1


def test_stored_rows_are_sorted(staffed):
    write_timesheet(staffed, "2026-W01", [entry("E002", "2026-01-05", "8"), entry("E001", "2026-01-06", "8"),
                                         entry("E001", "2026-01-05", "8")])
    rows = read_timesheet(staffed, "2026-W01")
    assert [(row.employee_id, row.day.isoformat()) for row in rows] == [
        ("E001", "2026-01-05"), ("E001", "2026-01-06"), ("E002", "2026-01-05")]


def test_add_and_remove_single_rows(staffed, settings):
    add_entry(staffed, settings, "2026-W01", "E001", "2026-01-05", "8")
    add_entry(staffed, settings, "2026-W01", "E001", "2026-01-05", "2", "sick")
    with pytest.raises(PayrollError, match="duplicate row for E001 on 2026-01-05"):
        add_entry(staffed, settings, "2026-W01", "E001", "2026-01-05", "1")
    assert remove_entries(staffed, settings, "2026-W01", "E001", "2026-01-05", "sick") == 1
    assert [row.kind for row in read_timesheet(staffed, "2026-W01")] == ["work"]


def test_blank_sheet_has_a_row_per_day(staffed, settings):
    lines = blank_sheet(staffed, settings, "2026-W01").splitlines()
    assert lines[0] == "employee_id,date,hours,kind"
    assert len(lines) == 1 + 2 * 7
