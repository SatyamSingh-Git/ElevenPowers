import pytest

from throttle import ManualClock, RateLimitExceeded, Throttle, TokenBucket


def test_check_raises_value_error_not_rate_limit():
    throttle = Throttle(ManualClock(), default='10/minute')
    with pytest.raises(ValueError) as caught:
        throttle.check('upload', cost=15)
    assert not isinstance(caught.value, RateLimitExceeded)
    assert str(caught.value) == 'cost must be between 1 and 10: 15'


def test_refused_hit_spends_nothing():
    clock = ManualClock()
    throttle = Throttle(clock, default='10/minute; algorithm=sliding')
    throttle.hit('k', 4)
    with pytest.raises(ValueError):
        throttle.check('k', cost=12)
    decision = throttle.hit('k', 6)
    assert decision.allowed and decision.remaining == 0


def test_bucket_limit_is_its_capacity():
    bucket = TokenBucket(4, 8, ManualClock())
    with pytest.raises(ValueError) as caught:
        bucket.hit(5)
    assert str(caught.value) == 'cost must be between 1 and 4: 5'
    assert bucket.peek().remaining == 4
