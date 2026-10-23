import pytest

from cronish import SHORTCUTS, JobFileError, ScheduleError, load_jobs, parse


def selected(schedule):
    return (schedule.minutes, schedule.hours, schedule.days, schedule.months, schedule.weekdays)


def test_numbers_stars_lists_ranges_and_steps():
    schedule = parse("5 4 * * *")
    assert schedule.minutes == (5,)
    assert schedule.hours == (4,)
    assert schedule.days == tuple(range(1, 32))
    assert schedule.months == tuple(range(1, 13))
    schedule = parse("*/20 9-17/4 1,15 jan,JUL mon-fri")
    assert schedule.minutes == (0, 20, 40)
    assert schedule.hours == (9, 13, 17)
    assert schedule.days == (1, 15)
    assert schedule.months == (1, 7)
    assert schedule.weekdays == (1, 2, 3, 4, 5)
    assert parse("5/15 * * * *").minutes == (5, 20, 35, 50)


def test_shortcuts_mean_their_expansions():
    assert selected(parse("@daily")) == selected(parse("0 0 * * *"))
    assert selected(parse("@hourly")) == selected(parse("0 * * * *"))
    assert selected(parse("@monthly")) == selected(parse("0 0 1 * *"))
    assert selected(parse("@yearly")) == selected(parse("0 0 1 1 *"))
    assert selected(parse("@weekly")) == selected(parse("0 0 * * sun"))
    assert selected(parse("@Weekly")) == selected(parse("@weekly"))
    assert set(SHORTCUTS) >= {"@yearly", "@monthly", "@weekly", "@daily", "@hourly"}


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("61 * * * *", "minute: value 61 out of range 0-59"),
        ("* 24 * * *", "hour: value 24 out of range 0-23"),
        ("* * 32 * *", "day: value 32 out of range 1-31"),
        ("* * *", "expression: expected 5 fields, got 3"),
        ("* * * foo *", "month: unknown name 'foo'"),
        ("@often", "expression: unknown shortcut '@often'"),
        ("5-1 * * * *", "minute: range 5-1 runs backwards"),
        ("* 1x * * *", "hour: cannot parse '1x'"),
    ],
)
def test_parse_errors(text, message):
    with pytest.raises(ScheduleError) as caught:
        parse(text)
    assert str(caught.value) == message
    assert isinstance(caught.value, ValueError)


def test_jobs_file_is_read():
    jobs = load_jobs("# nightly\nbackup 0 2 * * *\n\nreport\t30 9 * * mon-fri\n")
    assert [job.name for job in jobs] == ["backup", "report"]
    assert jobs[1].schedule.minutes == (30,)


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("a * * * * *\nb 61 * * * *", "line 2: minute: value 61 out of range 0-59"),
        ("a 0 0 30 2 *", "line 1: day: no selected month has a day 30"),
        ("a * * 1 * *\n\nb 0 0 * * mon,foo", "line 3: weekday: unknown name 'foo'"),
        ("a * * * * *\na 0 * * * *", "line 2: duplicate job 'a'"),
        ("a/b * * * * *", "line 1: invalid job name 'a/b'"),
    ],
)
def test_jobs_file_errors(text, message):
    with pytest.raises(JobFileError) as caught:
        load_jobs(text)
    assert str(caught.value) == message
