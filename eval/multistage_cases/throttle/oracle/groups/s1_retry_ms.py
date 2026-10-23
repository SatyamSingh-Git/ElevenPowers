from throttle import ManualClock, Throttle


def test_fixed_window_wait_in_milliseconds():
    clock = ManualClock()
    throttle = Throttle(clock, default='3/minute')
    clock.advance(20)
    for _ in range(3):
        assert throttle.hit('a').retry_after == 0
    denied = throttle.hit('a')
    assert denied.retry_after == 40000
    assert isinstance(denied.retry_after, int)


def test_sliding_and_bucket_waits_in_milliseconds():
    clock = ManualClock()
    throttle = Throttle(clock)
    throttle.set_policy('s:*', '2/10s; algorithm=sliding')
    throttle.set_policy('b:*', '2/second; algorithm=bucket')
    throttle.hit('s:1')
    clock.advance(2.5)
    throttle.hit('s:1')
    assert throttle.hit('s:1').retry_after == 7500
    throttle.hit('b:1', 2)
    denied = throttle.hit('b:1')
    assert denied.retry_after == 500
    assert isinstance(denied.retry_after, int)


def test_snapshot_wait_matches_decision():
    clock = ManualClock()
    throttle = Throttle(clock, default='1/10s; algorithm=sliding')
    throttle.hit('k')
    clock.advance(4)
    throttle.hit('fresh')
    entries = {entry['key']: entry for entry in throttle.snapshot()}
    assert entries['k']['retry_after'] == 6000
    assert entries['fresh']['retry_after'] == 10000
