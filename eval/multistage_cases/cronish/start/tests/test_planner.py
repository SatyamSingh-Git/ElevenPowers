from datetime import datetime, timedelta, timezone

import pytest

from cronish import ScheduleError, next_runs, parse, previous_run, runs_between

WEDNESDAY = datetime(2024, 3, 6, 10, 17, 30)


def test_weekday_runs():
    assert next_runs(parse("30 9 * * mon-fri"), WEDNESDAY, 3) == [
        datetime(2024, 3, 7, 9, 30),
        datetime(2024, 3, 8, 9, 30),
        datetime(2024, 3, 11, 9, 30),
    ]


def test_sunday_runs():
    assert next_runs(parse("0 10 * * sun"), WEDNESDAY, 2) == [
        datetime(2024, 3, 10, 10, 0),
        datetime(2024, 3, 17, 10, 0),
    ]


def test_default_count_starts_at_the_next_whole_minute():
    runs = next_runs(parse("* * * * *"), WEDNESDAY)
    assert len(runs) == 5
    assert runs[0] == datetime(2024, 3, 6, 10, 18)


def test_a_run_exactly_at_now_is_listed():
    now = datetime(2024, 3, 6, 9, 0)
    assert next_runs(parse("0 9 * * *"), now, 1) == [now]


def test_day_and_weekday_both_restricted_means_either():
    assert next_runs(parse("0 0 13 * fri"), WEDNESDAY, 3) == [
        datetime(2024, 3, 8),
        datetime(2024, 3, 13),
        datetime(2024, 3, 15),
    ]


def test_leap_day_is_found_years_ahead():
    assert next_runs(parse("0 0 29 2 *"), datetime(2025, 1, 1), 1) == [datetime(2028, 2, 29)]


def test_a_schedule_that_never_runs():
    with pytest.raises(ScheduleError, match="no run within 5 years"):
        next_runs(parse("0 0 30 2 *"), WEDNESDAY)


@pytest.mark.parametrize("count", [0, 101])
def test_count_limits(count):
    with pytest.raises(ScheduleError, match="count must be between 1 and 100"):
        next_runs(parse("* * * * *"), WEDNESDAY, count)


def test_aware_times_keep_their_zone():
    zone = timezone(timedelta(hours=2))
    now = datetime(2024, 3, 6, 10, 0, tzinfo=zone)
    assert next_runs(parse("30 10 * * *"), now, 1) == [datetime(2024, 3, 6, 10, 30, tzinfo=zone)]


def test_previous_run():
    assert previous_run(parse("0 10 * * sun"), WEDNESDAY) == datetime(2024, 3, 3, 10, 0)
    assert previous_run(parse("17 10 * * *"), WEDNESDAY) == datetime(2024, 3, 6, 10, 17)


def test_runs_between_excludes_the_end():
    runs = runs_between(parse("0 */6 * * *"), datetime(2024, 3, 6), datetime(2024, 3, 6, 18))
    assert runs == [datetime(2024, 3, 6, 0), datetime(2024, 3, 6, 6), datetime(2024, 3, 6, 12)]
