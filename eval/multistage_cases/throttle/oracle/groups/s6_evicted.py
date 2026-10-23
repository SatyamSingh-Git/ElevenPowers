from throttle import ManualClock, Throttle, load_config, summarise


def test_summary_counts_evictions():
    throttle = Throttle(ManualClock(), max_keys=2)
    assert summarise(throttle)['evicted'] == 0
    for key in ('a', 'b', 'c', 'd', 'a'):
        throttle.hit(key)
    summary = summarise(throttle)
    assert summary['evicted'] == 3
    assert summary['keys'] == 2


def test_hits_on_tracked_keys_evict_nothing():
    throttle = load_config('max_keys = 3\n', ManualClock())
    for _ in range(4):
        for key in ('x', 'y', 'z'):
            throttle.hit(key)
    assert summarise(throttle)['evicted'] == 0
