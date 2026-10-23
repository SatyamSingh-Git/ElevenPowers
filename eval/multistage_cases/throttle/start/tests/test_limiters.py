import pytest

from throttle import FixedWindow, ManualClock, SlidingWindow, TokenBucket


def test_clock_cannot_go_backwards():
    clock = ManualClock(10)
    with pytest.raises(ValueError, match='clock cannot go backwards'):
        clock.advance(-1)
    assert clock.set(15) == 15


def test_fixed_window_resets_on_boundary():
    clock = ManualClock()
    window = FixedWindow(2, 10, clock)
    clock.advance(4)
    assert window.hit().remaining == 1
    assert window.hit().remaining == 0
    denied = window.hit()
    assert not denied.allowed
    assert denied.retry_after == 6
    clock.advance(6)
    assert window.hit().allowed


def test_fixed_window_state():
    clock = ManualClock()
    window = FixedWindow(5, 60, clock)
    assert window.state() == {'kind': 'fixed', 'limit': 5, 'remaining': 5, 'reset_in': 0.0}
    clock.advance(20)
    window.hit(2)
    assert window.state() == {'kind': 'fixed', 'limit': 5, 'remaining': 3, 'reset_in': 40.0}


def test_sliding_window_frees_oldest_first():
    clock = ManualClock()
    window = SlidingWindow(3, 10, clock)
    window.hit()
    clock.advance(4)
    window.hit(2)
    denied = window.hit(2)
    assert not denied.allowed
    assert denied.retry_after == 10
    assert window.hit().retry_after == 6
    clock.advance(6)
    assert window.hit().allowed
    assert window.state()['reset_in'] == 10


def test_bucket_refills_continuously():
    clock = ManualClock()
    bucket = TokenBucket(4, 2.0, clock)
    assert bucket.hit(4).remaining == 0
    denied = bucket.hit()
    assert denied.retry_after == 0.5
    clock.advance(1)
    assert bucket.peek().remaining == 2
    assert bucket.state() == {'kind': 'bucket', 'limit': 4, 'remaining': 2, 'reset_in': 1.0}


@pytest.mark.parametrize('make', [
    lambda clock: FixedWindow(0, 10, clock),
    lambda clock: SlidingWindow(-1, 10, clock),
    lambda clock: TokenBucket(0, 1.0, clock),
])
def test_limit_must_be_positive(make):
    with pytest.raises(ValueError, match='limit must be positive'):
        make(ManualClock())


def test_bucket_rate_must_be_positive():
    with pytest.raises(ValueError, match='refill_per_second must be positive: 0'):
        TokenBucket(5, 0, ManualClock())


def test_cost_must_be_at_least_one():
    with pytest.raises(ValueError, match='cost must be at least 1: 0'):
        FixedWindow(5, 10, ManualClock()).hit(0)
