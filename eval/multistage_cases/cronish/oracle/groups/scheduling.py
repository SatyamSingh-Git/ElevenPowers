from datetime import datetime

import pytest

from cronish import ScheduleError, describe, due_jobs, load_jobs, next_runs, parse, previous_run, upcoming

WEDNESDAY = datetime(2024, 3, 6, 10, 17, 30)

JOBS = "backup 0 10 * * sun\nreport 30 9 * * mon-fri\ntick * * * * *\n"


def test_weekday_schedules():
    assert next_runs(parse("30 9 * * mon-fri"), WEDNESDAY, 3) == [
        datetime(2024, 3, 7, 9, 30),
        datetime(2024, 3, 8, 9, 30),
        datetime(2024, 3, 11, 9, 30),
    ]


def test_sunday_schedules():
    assert next_runs(parse("0 10 * * sun"), WEDNESDAY, 2) == [datetime(2024, 3, 10, 10), datetime(2024, 3, 17, 10)]
    assert next_runs(parse("@weekly"), WEDNESDAY, 1) == [datetime(2024, 3, 10)]
    assert next_runs(parse("0 8 * * sat,sun"), WEDNESDAY, 2) == [datetime(2024, 3, 9, 8), datetime(2024, 3, 10, 8)]
    assert previous_run(parse("0 10 * * sun"), WEDNESDAY) == datetime(2024, 3, 3, 10)


def test_day_or_weekday():
    assert next_runs(parse("0 0 13 * fri"), WEDNESDAY, 3) == [
        datetime(2024, 3, 8),
        datetime(2024, 3, 13),
        datetime(2024, 3, 15),
    ]


def test_default_count_and_partial_minutes():
    runs = next_runs(parse("* * * * *"), WEDNESDAY)
    assert runs == [datetime(2024, 3, 6, 10, minute) for minute in range(18, 23)]


def test_leap_day_and_never():
    assert next_runs(parse("0 0 29 2 *"), datetime(2025, 1, 1), 1) == [datetime(2028, 2, 29)]
    with pytest.raises(ScheduleError) as caught:
        next_runs(parse("0 0 30 2 *"), WEDNESDAY)
    assert str(caught.value) == "no run within 5 years"


def test_weekday_names_in_descriptions():
    assert "Sunday" in describe(parse("0 10 * * sun"))
    words = describe(parse("0 8 * * sat,sun"))
    assert "Saturday" in words and "Sunday" in words
    assert "Monday" in describe(parse("0 8 * * mon"))


def test_due_jobs():
    jobs = load_jobs(JOBS)
    assert due_jobs(jobs, datetime(2024, 3, 10, 10, 0)) == ["backup", "tick"]
    assert due_jobs(jobs, datetime(2024, 3, 11, 9, 30, 45)) == ["report", "tick"]
    assert due_jobs(jobs, datetime(2024, 3, 11, 9, 31)) == ["tick"]


def test_upcoming_across_jobs():
    jobs = load_jobs(JOBS)[:2]
    assert upcoming(jobs, WEDNESDAY, 3) == [
        (datetime(2024, 3, 7, 9, 30), "report"),
        (datetime(2024, 3, 8, 9, 30), "report"),
        (datetime(2024, 3, 10, 10, 0), "backup"),
    ]
