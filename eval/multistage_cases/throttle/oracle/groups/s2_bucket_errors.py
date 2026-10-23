import pytest

from throttle import ManualClock, TokenBucket


@pytest.mark.parametrize('period', [0, -5])
def test_refill_period_must_be_positive(period):
    with pytest.raises(ValueError) as caught:
        TokenBucket(5, period, ManualClock())
    assert str(caught.value) == f'refill_period must be positive: {period}'


def test_slow_refill():
    clock = ManualClock()
    bucket = TokenBucket(2, 3600, clock)
    bucket.hit(2)
    assert bucket.hit().retry_after == 1_800_000
    clock.advance(1800)
    assert bucket.hit().allowed
