from throttle import ManualClock, Throttle, render_table


def entry(throttle, key):
    return next(item for item in throttle.snapshot() if item['key'] == key)


def test_bucket_reset_at_stays_put_as_it_refills():
    clock = ManualClock(100)
    throttle = Throttle(clock, default='1/second; algorithm=bucket; burst=4')
    throttle.hit('b', 4)
    clock.advance(1.5)
    assert entry(throttle, 'b')['reset_at'] == 104
    clock.advance(1)
    assert entry(throttle, 'b')['reset_at'] == 104
    assert 'reset_in' not in entry(throttle, 'b')


def test_full_bucket_resets_now():
    clock = ManualClock(50)
    throttle = Throttle(clock, default='1/second; algorithm=bucket; burst=4')
    throttle.hit('b')
    clock.advance(10)
    assert entry(throttle, 'b')['reset_at'] == 60


def test_table_still_shows_time_left_from_a_late_start():
    clock = ManualClock(1000)
    throttle = Throttle(clock, default='1/second; algorithm=bucket; burst=4')
    throttle.set_policy('w', '5/minute')
    throttle.hit('b', 4)
    throttle.hit('w')
    clock.advance(1)
    assert render_table(throttle) == (
        'key  policy                               remaining  retry  resets\n'
        'b    1/second; algorithm=bucket; burst=4  1/4        -      3s\n'
        'w    5/minute                             4/5        -      19s\n'
    )
