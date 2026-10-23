import pytest

from throttle import FixedWindow, ManualClock, Policy, PolicyError, SlidingWindow, TokenBucket
from throttle import build_limiter, format_policy, parse_policy


def test_parse_simple_policy():
    assert parse_policy('100/minute') == Policy(100, 60.0)


def test_parse_options():
    policy = parse_policy('10 / 30s ; algorithm=bucket; burst=25')
    assert policy == Policy(10, 30.0, 'bucket', 25)
    assert policy.capacity == 25


@pytest.mark.parametrize('text, message', [
    ('fast', 'invalid policy: fast'),
    ('10/fortnight', 'unknown unit: fortnight'),
    ('0/minute', 'limit must be positive: 0'),
    ('5/minute; algorithm=leaky', 'unknown algorithm: leaky'),
    ('5/minute; colour=red', 'unknown option: colour'),
    ('5/minute; bucket', 'invalid option: bucket'),
    ('5/minute; algorithm=bucket; burst=0', 'burst must be a positive integer: 0'),
    ('5/minute; burst=3', 'burst only applies to the bucket algorithm'),
])
def test_parse_errors(text, message):
    with pytest.raises(PolicyError) as caught:
        parse_policy(text)
    assert str(caught.value) == message


@pytest.mark.parametrize('text', [
    '100/minute', '5/30s; algorithm=sliding', '3/2h', '10/second; algorithm=bucket; burst=50', '4/500ms',
])
def test_format_round_trips(text):
    assert format_policy(parse_policy(text)) == text


def test_build_limiter_picks_algorithm():
    clock = ManualClock()
    assert isinstance(build_limiter(parse_policy('5/minute'), clock), FixedWindow)
    assert isinstance(build_limiter(parse_policy('5/minute; algorithm=sliding'), clock), SlidingWindow)
    assert isinstance(build_limiter(parse_policy('5/minute; algorithm=bucket'), clock), TokenBucket)


def test_bucket_policy_refills_at_policy_rate():
    clock = ManualClock()
    bucket = build_limiter(parse_policy('60/minute; algorithm=bucket; burst=10'), clock)
    for _ in range(10):
        assert bucket.hit().allowed
    assert not bucket.hit().allowed
    clock.advance(3)
    assert bucket.peek().remaining == 3
