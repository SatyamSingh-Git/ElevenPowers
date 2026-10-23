import pytest

from cronish import SHORTCUTS, ScheduleError, parse
from cronish.fields import DAY, MONTH, parse_field


def selected(schedule):
    return (schedule.minutes, schedule.hours, schedule.days, schedule.months, schedule.weekdays)


def test_plain_numbers_and_stars():
    schedule = parse("5 4 * * *")
    assert schedule.minutes == (5,)
    assert schedule.hours == (4,)
    assert schedule.days == tuple(range(1, 32))
    assert schedule.months == tuple(range(1, 13))
    assert schedule.day_star and schedule.weekday_star


def test_lists_ranges_steps_and_names():
    schedule = parse("*/20 9-17/4 1,15 jan,JUL mon-fri")
    assert schedule.minutes == (0, 20, 40)
    assert schedule.hours == (9, 13, 17)
    assert schedule.days == (1, 15)
    assert schedule.months == (1, 7)
    assert schedule.weekdays == (1, 2, 3, 4, 5)
    assert not schedule.day_star and not schedule.weekday_star


def test_step_from_a_single_value_runs_to_the_end_of_the_field():
    assert parse_field("5/15", DAY) == (5, 20)
    assert parse("5/15 * * * *").minutes == (5, 20, 35, 50)


def test_month_names_are_numbered_from_one():
    assert parse_field("dec", MONTH) == (12,)


@pytest.mark.parametrize("shortcut", sorted(SHORTCUTS))
def test_shortcuts_match_their_expansion(shortcut):
    assert selected(parse(shortcut)) == selected(parse(SHORTCUTS[shortcut]))


def test_shortcuts_ignore_case_and_keep_their_text():
    assert parse("@Daily").expression == "@Daily"
    assert str(parse("  0   9 * *  * ")) == "0 9 * * *"


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("61 * * * *", "minute: value 61 out of range 0-59"),
        ("* 24 * * *", "hour: value 24 out of range 0-23"),
        ("* * 0 * *", "day: value 0 out of range 1-31"),
        ("* * *", "expression: expected 5 fields, got 3"),
        ("* * * foo *", "month: unknown name 'foo'"),
        ("@often", "expression: unknown shortcut '@often'"),
        ("5-1 * * * *", "minute: range 5-1 runs backwards"),
        ("* 1x * * *", "hour: cannot parse '1x'"),
        ("*/x * * * *", "minute: cannot parse '*/x'"),
    ],
)
def test_errors_name_the_field(text, message):
    with pytest.raises(ScheduleError) as caught:
        parse(text)
    assert str(caught.value) == message


def test_schedule_error_is_a_value_error():
    assert issubclass(ScheduleError, ValueError)
