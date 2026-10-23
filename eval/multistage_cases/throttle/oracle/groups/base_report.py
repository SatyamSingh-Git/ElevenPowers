import csv
import io

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


def test_table():
    assert render_table(busy_throttle()) == (
        'key  policy                               remaining  retry  resets\n'
        'b:1  1/second; algorithm=bucket; burst=4  2/4        -      1.5s\n'
        's:1  2/10s; algorithm=sliding             0/2        7.5s   7.5s\n'
        'web  10/minute                            7/10       -      57.5s\n'
    )


def test_table_after_time_passes():
    throttle = busy_throttle()
    throttle.clock.advance(1)
    lines = render_table(throttle).splitlines()
    assert lines[1].split() == ['b:1', '1/second;', 'algorithm=bucket;', 'burst=4', '3/4', '-', '500ms']
    assert lines[2].split() == ['s:1', '2/10s;', 'algorithm=sliding', '0/2', '6.5s', '6.5s']


def test_summary():
    summary = summarise(busy_throttle())
    assert (summary['keys'], summary['exhausted'], summary['busiest']) == (3, 1, 's:1')
    assert render_summary(busy_throttle()) == '3 keys, 1 exhausted, busiest: s:1'
    assert nearest_limit(busy_throttle(), 2) == [('s:1', 0, 2), ('b:1', 2, 4)]


def test_csv_rows():
    rows = list(csv.DictReader(io.StringIO(to_csv(busy_throttle()))))
    assert [(row['key'], row['remaining'], row['limit']) for row in rows] == [
        ('b:1', '2', '4'), ('s:1', '0', '2'), ('web', '7', '10')]
    assert to_csv(Throttle(ManualClock())) == ''
