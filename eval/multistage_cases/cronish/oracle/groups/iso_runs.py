from datetime import datetime

from cronish import describe, next_runs, parse, previous_run, runs_between

WEDNESDAY = datetime(2024, 3, 6, 10, 17, 30)


def test_runs_on_day_seven_fall_on_sunday():
    assert next_runs(parse("0 8 * * 7"), WEDNESDAY, 2) == [datetime(2024, 3, 10, 8), datetime(2024, 3, 17, 8)]
    assert next_runs(parse("0 8 * * 6,7"), WEDNESDAY, 2) == [datetime(2024, 3, 9, 8), datetime(2024, 3, 10, 8)]
    assert previous_run(parse("0 8 * * 7"), WEDNESDAY) == datetime(2024, 3, 3, 8)


def test_runs_on_day_one_fall_on_monday():
    assert next_runs(parse("0 8 * * 1"), WEDNESDAY, 1) == [datetime(2024, 3, 11, 8)]
    week = runs_between(parse("0 12 * * 1-7"), datetime(2024, 3, 11), datetime(2024, 3, 18))
    assert [run.isoweekday() for run in week] == [1, 2, 3, 4, 5, 6, 7]


def test_day_or_weekday_with_seven():
    assert next_runs(parse("0 0 13 * 7"), WEDNESDAY, 3) == [
        datetime(2024, 3, 10),
        datetime(2024, 3, 13),
        datetime(2024, 3, 17),
    ]


def test_descriptions_name_the_iso_days():
    words = describe(parse("0 8 * * 7"))
    assert "Sunday" in words and "Monday" not in words
    words = describe(parse("0 8 * * 1"))
    assert "Monday" in words and "Sunday" not in words
    words = describe(parse("0 8 * * 6,7"))
    assert "Saturday" in words and "Sunday" in words
