import io

from eventlog import Log, LogConfig
from eventlog.cli import main


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    return main(list(argv), out, err), out.getvalue(), err.getvalue()


def test_dump(tmp_path):
    with Log.open(tmp_path) as log:
        log.append('a', 'one', timestamp=5)
        log.delete('a', timestamp=6)
    assert run('dump', str(tmp_path)) == (0, '0\t5\ta\tone\n1\t6\ta\t<deleted>\n', '')
    assert run('dump', str(tmp_path), '--from', '1')[1] == '1\t6\ta\t<deleted>\n'


def test_dump_reports_errors(tmp_path):
    Log.open(tmp_path).close()
    code, out, err = run('dump', str(tmp_path), '--from', '5')
    assert (code, out) == (1, '')
    assert err == 'eventlog: offset 5 is outside 0..0\n'


def test_stats(tmp_path):
    Log.open(tmp_path).close()
    assert run('stats', str(tmp_path))[1].startswith('segments: 1\nrecords: 0\n')


def test_compact(tmp_path):
    with Log.open(tmp_path, LogConfig(segment_bytes=100)) as log:
        for n in range(10):
            log.append('k', str(n))
    code, out, _ = run('compact', str(tmp_path))
    assert code == 0 and out.startswith('rewrote ')
