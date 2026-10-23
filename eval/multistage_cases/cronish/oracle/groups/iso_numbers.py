import pytest

from cronish import ScheduleError, parse, validate
from cronish.cli import main


def test_seven_is_sunday():
    assert parse("0 0 * * 7").weekdays == (7,)
    assert parse("* * * * sun").weekdays == (7,)
    assert parse("* * * * SUN").weekdays == (7,)
    assert parse("@weekly").weekdays == (7,)


def test_monday_is_one():
    assert parse("* * * * 1").weekdays == (1,)
    assert parse("* * * * mon").weekdays == (1,)
    assert parse("* * * * mon-sun").weekdays == (1, 2, 3, 4, 5, 6, 7)
    assert parse("* * * * 6-7").weekdays == (6, 7)


def test_zero_is_out_of_range():
    with pytest.raises(ScheduleError) as caught:
        parse("* * * * 0")
    assert str(caught.value) == "weekday: value 0 out of range 1-7"
    assert validate("* * * * 0") != []
    assert validate("* * * * 7") == []


def test_check_command(capsys):
    assert main(["check", "0 9 * * 7"]) == 0
    assert capsys.readouterr().out == "ok\n"
    assert main(["check", "0 9 * * 0"]) == 1
    assert "weekday: value 0 out of range 1-7" in capsys.readouterr().out
