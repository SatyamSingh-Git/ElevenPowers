import pytest

from throttle import ManualClock, Policy, RateLimitExceeded, Throttle


def test_default_policy_applies_to_unknown_keys():
    throttle = Throttle(ManualClock())
    assert throttle.policy_for('anyone') == Policy(60, 60.0)
    assert throttle.max_keys == 1000


def test_longest_pattern_wins():
    throttle = Throttle(ManualClock(), default='100/minute')
    throttle.set_policy('api:*', '10/minute')
    throttle.set_policy('api:admin:*', '1000/minute')
    throttle.set_policy('api:admin:eve', '1/minute')
    assert throttle.policy_for('api:bob').limit == 10
    assert throttle.policy_for('api:admin:ann').limit == 1000
    assert throttle.policy_for('api:admin:eve').limit == 1
    assert throttle.policy_for('web').limit == 100


def test_check_raises_with_wait():
    clock = ManualClock()
    throttle = Throttle(clock, default='2/minute')
    throttle.check('k')
    clock.advance(15)
    throttle.check('k')
    with pytest.raises(RateLimitExceeded) as caught:
        throttle.check('k')
    assert str(caught.value) == 'rate limit exceeded for k: retry in 45s'
    assert caught.value.key == 'k'


def test_changing_policy_restarts_affected_keys():
    throttle = Throttle(ManualClock(), default='2/minute')
    throttle.hit('a')
    throttle.hit('b')
    throttle.set_policy('a', '5/minute')
    assert throttle.keys() == ['b']
    assert throttle.remaining('a') == 5
    throttle.remove_policy('a')
    assert throttle.remaining('a') == 2


def test_least_recently_used_key_is_evicted():
    throttle = Throttle(ManualClock(), max_keys=2)
    throttle.hit('a')
    throttle.hit('b')
    throttle.hit('a')
    throttle.hit('c')
    assert sorted(throttle.keys()) == ['a', 'c']


def test_max_keys_must_be_positive():
    with pytest.raises(ValueError, match='max_keys must be at least 1: 0'):
        Throttle(ManualClock(), max_keys=0)


def test_limited_decorator():
    throttle = Throttle(ManualClock(), default='1/minute')

    @throttle.limited('job')
    def run():
        return 'ran'

    assert run() == 'ran'
    with pytest.raises(RateLimitExceeded):
        run()


def test_snapshot_lists_keys_in_order():
    clock = ManualClock()
    throttle = Throttle(clock, default='3/minute')
    throttle.hit('b')
    throttle.hit('a', 3)
    clock.advance(20)
    first, second = throttle.snapshot()
    assert first == {'key': 'a', 'policy': '3/minute', 'kind': 'fixed', 'limit': 3, 'remaining': 0,
                     'reset_in': 40.0, 'retry_after': 40.0}
    assert second['key'] == 'b' and second['remaining'] == 2
