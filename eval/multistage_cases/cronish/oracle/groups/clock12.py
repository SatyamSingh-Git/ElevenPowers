import pytest

from cronish import describe, parse


@pytest.mark.parametrize(
    ("text", "words"),
    [
        ("30 9 * * *", "at 9:30 AM, every day"),
        ("0 0 * * *", "at 12:00 AM, every day"),
        ("0 12 * * *", "at 12:00 PM, every day"),
        ("5 12 * * *", "at 12:05 PM, every day"),
        ("45 23 * * fri", "at 11:45 PM, on Friday"),
        ("0 9,17 1 * *", "at 9:00 AM and 5:00 PM, on day 1 of the month"),
        ("@daily", "at 12:00 AM, every day"),
    ],
)
def test_twelve_hour_descriptions(text, words):
    assert describe(parse(text)) == words
