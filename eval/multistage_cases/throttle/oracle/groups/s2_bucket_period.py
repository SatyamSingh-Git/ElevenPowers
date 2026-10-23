from throttle import ManualClock, TokenBucket


def test_empty_bucket_is_full_after_the_refill_period():
    clock = ManualClock()
    bucket = TokenBucket(10, 60, clock)
    assert bucket.hit(10).allowed
    assert bucket.hit().retry_after == 6000
    clock.advance(6)
    assert bucket.peek().remaining == 1
    clock.advance(54)
    assert bucket.peek().remaining == 10
    clock.advance(600)
    assert bucket.peek().remaining == 10


def test_refill_period_by_keyword():
    clock = ManualClock()
    bucket = TokenBucket(capacity=4, refill_period=2, clock=clock)
    bucket.hit(4)
    clock.advance(1)
    assert bucket.peek().remaining == 2
    assert bucket.hit(3).retry_after == 500
