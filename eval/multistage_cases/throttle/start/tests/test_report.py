from throttle import ManualClock, Throttle, nearest_limit, render_summary, render_table, summarise, to_csv


def busy_throttle():
    clock = ManualClock()
    throttle = Throttle(clock, default='10/minute')
    throttle.set_policy('s:*', '2/10s; algorithm=sliding')
    throttle.set_policy('b:*', '1/second; algorithm=bucket; burst=4')
    throttle.hit('web', 3)
    throttle.hit('s:1', 2)
    throttle.hit('b:1', 4)
    clock.advance(2.5)
    return throttle


def test_render_table():
    assert render_table(busy_throttle()) == (
        'key  policy                               remaining  retry  resets\n'
        'b:1  1/second; algorithm=bucket; burst=4  2/4        -      1.5s\n'
        's:1  2/10s; algorithm=sliding             0/2        7.5s   7.5s\n'
        'web  10/minute                            7/10       -      57.5s\n'
    )


def test_summarise():
    assert summarise(busy_throttle()) == {'keys': 3, 'exhausted': 1, 'busiest': 's:1'}
    assert render_summary(busy_throttle()) == '3 keys, 1 exhausted, busiest: s:1'
    assert render_summary(Throttle(ManualClock())) == 'no keys tracked'


def test_nearest_limit():
    assert nearest_limit(busy_throttle(), 2) == [('s:1', 0, 2), ('b:1', 2, 4)]


def test_csv():
    lines = to_csv(busy_throttle()).splitlines()
    assert lines[0] == 'key,policy,kind,limit,remaining,reset_in,retry_after'
    assert lines[2] == 's:1,2/10s; algorithm=sliding,sliding,2,0,7.5,7.5'
    assert to_csv(Throttle(ManualClock())) == ''
