from cronish import validate
from cronish.cli import main


def test_every_problem_is_reported():
    assert validate("61 25 * * *") == [
        ("minute", "value 61 out of range 0-59"),
        ("hour", "value 25 out of range 0-23"),
    ]
    assert validate("* * 0 13 mon-funday") == [
        ("day", "value 0 out of range 1-31"),
        ("month", "value 13 out of range 1-12"),
        ("weekday", "unknown name 'funday'"),
    ]


def test_check_lists_every_problem(capsys):
    assert main(["check", "61 25 * foo *"]) == 1
    assert capsys.readouterr().out == (
        "minute: value 61 out of range 0-59\nhour: value 25 out of range 0-23\nmonth: unknown name 'foo'\n"
    )
