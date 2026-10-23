import pytest

from cronish import describe, parse


@pytest.mark.parametrize(
    ("text", "words"),
    [
        ("* * * * *", "every minute, every day"),
        ("30 9 * * *", "at 09:30, every day"),
        ("0 9,17 * * *", "at 09:00 and 17:00, every day"),
        ("0 */6 * * *", "at 00:00, 06:00, 12:00 and 18:00, every day"),
        ("*/15 * * * *", "at minutes 0, 15, 30 and 45 past every hour, every day"),
        ("0,30 9-11 * * *", "at minutes 0 and 30 past hours 9, 10 and 11, every day"),
        ("* 9 * * *", "every minute during hour 9, every day"),
        ("0 10 * * sun", "at 10:00, on Sunday"),
        ("30 9 * * mon-fri", "at 09:30, on Monday, Tuesday, Wednesday, Thursday and Friday"),
        ("0 0 1,15 * *", "at 00:00, on days 1 and 15 of the month"),
        ("0 0 13 * fri", "at 00:00, on day 13 of the month or on Friday"),
        ("0 12 * jan,jul *", "at 12:00, every day, in January and July"),
        ("@weekly", "at 00:00, on Sunday"),
    ],
)
def test_descriptions(text, words):
    assert describe(parse(text)) == words
