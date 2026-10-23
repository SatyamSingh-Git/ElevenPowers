import time

import pytest

from throttle import ManualClock, RateLimitExceeded, Throttle


class Ticks:
    """Only what the time module offers: monotonic()."""

    def __init__(self, at):
        self.at = at

    def monotonic(self):
        return self.at


@pytest.mark.parametrize('policy, wait', [
    ('2/minute', 'retry in 50s'),
    ('2/minute; algorithm=sliding', 'retry in 1m'),
    ('2/minute; algorithm=bucket', 'retry in 30s'),
])
def test_throttle_runs_on_a_monotonic_clock(policy, wait):
    ticks = Ticks(1210)
    throttle = Throttle(ticks, default=policy)
    throttle.check('k')
    throttle.check('k')
    with pytest.raises(RateLimitExceeded) as caught:
        throttle.check('k')
    assert str(caught.value) == f'rate limit exceeded for k: {wait}'
    ticks.at += 60
    assert throttle.check('k').allowed


def test_time_module_is_a_clock():
    assert Throttle(time, default='5/minute').hit('k').allowed


def test_manual_clock_offers_monotonic():
    clock = ManualClock(5)
    assert clock.monotonic() == 5
    clock.advance(2.5)
    assert clock.monotonic() == 7.5
