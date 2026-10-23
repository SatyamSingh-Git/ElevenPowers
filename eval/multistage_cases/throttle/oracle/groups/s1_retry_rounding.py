from throttle import ManualClock, Throttle


def test_fraction_of_a_millisecond_rounds_up():
    throttle = Throttle(ManualClock(), default='3/second; algorithm=bucket')
    throttle.hit('k', 3)
    assert throttle.hit('k').retry_after == 334


def test_sliding_wait_rounds_up():
    clock = ManualClock()
    throttle = Throttle(clock, default='1/second; algorithm=sliding')
    throttle.hit('k')
    clock.advance(0.0004)
    assert throttle.hit('k').retry_after == 1000
