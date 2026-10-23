from throttle import FixedWindow, ManualClock, SlidingWindow, Throttle


def entry(throttle, key):
    return next(item for item in throttle.snapshot() if item['key'] == key)


def test_fixed_window_resets_at_the_window_end():
    clock = ManualClock(100)
    throttle = Throttle(clock, default='3/minute')
    throttle.hit('a')
    clock.advance(5)
    assert entry(throttle, 'a')['reset_at'] == 120
    assert 'reset_in' not in entry(throttle, 'a')
    clock.advance(30)
    assert entry(throttle, 'a')['reset_at'] == 135


def test_sliding_window_resets_when_the_newest_hit_ages_out():
    clock = ManualClock(100)
    throttle = Throttle(clock, default='2/10s; algorithm=sliding')
    throttle.hit('s')
    clock.advance(3)
    throttle.hit('s')
    clock.advance(1)
    assert entry(throttle, 's')['reset_at'] == 113
    clock.advance(4)
    assert entry(throttle, 's')['reset_at'] == 113
    clock.advance(7)
    assert entry(throttle, 's')['reset_at'] == 115


def test_limiter_state_directly():
    clock = ManualClock(7)
    window = FixedWindow(5, 10, clock)
    assert window.state()['reset_at'] == 7
    window.hit()
    assert window.state() == {'kind': 'fixed', 'limit': 5, 'remaining': 4, 'reset_at': 10}
    sliding = SlidingWindow(5, 10, clock)
    sliding.hit()
    assert sliding.state() == {'kind': 'sliding', 'limit': 5, 'remaining': 4, 'reset_at': 17}
