import pytest

from throttle import ManualClock, RateLimitExceeded, Throttle, load_config


def refusal(throttle, key):
    with pytest.raises(RateLimitExceeded) as caught:
        throttle.check(key)
    return str(caught.value)


def test_fixed_window_waits_for_the_boundary():
    clock = ManualClock()
    throttle = Throttle(clock, default='3/minute')
    clock.advance(20)
    for _ in range(3):
        assert throttle.hit('a').allowed
    assert not throttle.hit('a').allowed
    assert refusal(throttle, 'a') == 'rate limit exceeded for a: retry in 40s'
    clock.advance(40)
    assert throttle.check('a').allowed


def test_sliding_window_waits_for_the_oldest_hit():
    clock = ManualClock()
    throttle = Throttle(clock)
    throttle.set_policy('s:*', '2/10s; algorithm=sliding')
    throttle.check('s:1')
    clock.advance(2.5)
    throttle.check('s:1')
    assert refusal(throttle, 's:1') == 'rate limit exceeded for s:1: retry in 7.5s'
    clock.advance(7.5)
    throttle.check('s:1')
    assert refusal(throttle, 's:1') == 'rate limit exceeded for s:1: retry in 2.5s'


def test_bucket_policy_refills_at_the_policy_rate():
    clock = ManualClock()
    throttle = Throttle(clock)
    throttle.set_policy('b:*', '60/minute; algorithm=bucket; burst=5')
    for _ in range(5):
        throttle.check('b:1')
    assert refusal(throttle, 'b:1') == 'rate limit exceeded for b:1: retry in 1s'
    clock.advance(2)
    throttle.check('b:1')
    throttle.check('b:1')
    assert refusal(throttle, 'b:1') == 'rate limit exceeded for b:1: retry in 1s'


def test_slow_bucket_partial_wait():
    clock = ManualClock()
    throttle = Throttle(clock, default='1/4s; algorithm=bucket; burst=2')
    throttle.check('k')
    throttle.check('k')
    clock.advance(1)
    assert refusal(throttle, 'k') == 'rate limit exceeded for k: retry in 3s'
    clock.advance(3)
    assert throttle.check('k').allowed


def test_patterns_and_eviction():
    clock = ManualClock()
    throttle = Throttle(clock, default='100/minute', max_keys=2)
    throttle.set_policy('api:*', '1/minute')
    throttle.check('api:a')
    assert refusal(throttle, 'api:a') == 'rate limit exceeded for api:a: retry in 1m'
    throttle.hit('web')
    throttle.hit('api:a')
    throttle.hit('other')
    assert sorted(throttle.keys()) == ['api:a', 'other']


def test_config_policies_are_enforced():
    clock = ManualClock()
    throttle = load_config(
        'default = 2/minute\n'
        'limit login:* = 1/30s; algorithm=sliding\n'
        'limit up:* = 1/second; algorithm=bucket; burst=3\n',
        clock,
    )
    throttle.check('login:ann')
    clock.advance(10)
    assert refusal(throttle, 'login:ann') == 'rate limit exceeded for login:ann: retry in 20s'
    for _ in range(3):
        throttle.check('up:x')
    assert refusal(throttle, 'up:x') == 'rate limit exceeded for up:x: retry in 1s'
    throttle.check('home')
    throttle.check('home')
    assert refusal(throttle, 'home') == 'rate limit exceeded for home: retry in 50s'
