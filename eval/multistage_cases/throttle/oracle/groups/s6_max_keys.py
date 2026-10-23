from throttle import ManualClock, Throttle, load_config


def test_default_cap_is_ten_thousand():
    throttle = Throttle(ManualClock())
    for number in range(10_000):
        throttle.hit(f'user:{number}')
    assert len(throttle.keys()) == 10_000
    assert 'user:0' in throttle.keys()
    throttle.hit('one more')
    assert len(throttle.keys()) == 10_000
    assert 'user:0' not in throttle.keys()


def test_config_without_a_cap_uses_the_default():
    throttle = load_config('default = 5/minute\n', ManualClock())
    assert throttle.max_keys == 10_000
