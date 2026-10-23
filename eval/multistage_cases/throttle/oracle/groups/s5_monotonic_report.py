from throttle import Throttle, render_summary, render_table, summarise, to_csv


class Ticks:
    def __init__(self, at):
        self.at = at

    def monotonic(self):
        return self.at


def busy(ticks):
    throttle = Throttle(ticks, default='10/minute')
    throttle.set_policy('s:*', '2/10s; algorithm=sliding')
    throttle.set_policy('b:*', '1/second; algorithm=bucket; burst=4')
    throttle.hit('web', 3)
    throttle.hit('s:1', 2)
    throttle.hit('b:1', 4)
    ticks.at += 2.5
    return throttle


def test_table_on_a_monotonic_clock():
    assert render_table(busy(Ticks(600))) == (
        'key  policy                               remaining  retry  resets\n'
        'b:1  1/second; algorithm=bucket; burst=4  2/4        -      1.5s\n'
        's:1  2/10s; algorithm=sliding             0/2        7.5s   7.5s\n'
        'web  10/minute                            7/10       -      57.5s\n'
    )


def test_summaries_on_a_monotonic_clock():
    ticks = Ticks(600)
    throttle = busy(ticks)
    summary = summarise(throttle)
    assert (summary['keys'], summary['exhausted'], summary['busiest']) == (3, 1, 's:1')
    assert render_summary(throttle) == '3 keys, 1 exhausted, busiest: s:1'
    assert to_csv(throttle).splitlines()[0].startswith('key,policy,kind,limit,remaining')
