import pytest

from cronish import describe, parse


@pytest.mark.parametrize(
    ("text", "words"),
    [
        ("*/15 * * * *", "every 15 minutes, every day"),
        ("*/5 * * * *", "every 5 minutes, every day"),
        ("*/10 * * * mon", "every 10 minutes, on Monday"),
        ("*/10 9-11 * * *", "every 10 minutes during hours 9, 10 and 11, every day"),
    ],
)
def test_minute_intervals(text, words):
    assert describe(parse(text)) == words


def test_uneven_or_offset_minutes_are_still_listed():
    assert describe(parse("5/15 * * * *")) == "at minutes 5, 20, 35 and 50 past every hour, every day"
    assert describe(parse("*/7 * * * *")) == (
        "at minutes 0, 7, 14, 21, 28, 35, 42, 49 and 56 past every hour, every day"
    )
