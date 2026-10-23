import pytest

from cronish import ScheduleError, parse


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("*/0 * * * *", "minute: step must be at least 1"),
        ("0 1-10/0 * * *", "hour: step must be at least 1"),
        ("0 0 5/0 * *", "day: step must be at least 1"),
        ("0 0 * */0 *", "month: step must be at least 1"),
        ("0 0 * * mon-fri/0", "weekday: step must be at least 1"),
    ],
)
def test_zero_step_is_rejected(text, message):
    with pytest.raises(ScheduleError) as caught:
        parse(text)
    assert str(caught.value) == message


def test_other_steps_still_work():
    assert parse("*/1 * * * *").minutes == tuple(range(60))
    assert parse("0 1-10/3 * * *").hours == (1, 4, 7, 10)
