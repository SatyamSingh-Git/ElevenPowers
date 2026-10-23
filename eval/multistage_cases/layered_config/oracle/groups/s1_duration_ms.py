import io
import json

from layercfg.cli import main


def run(*argv, env=None):
    out, err = io.StringIO(), io.StringIO()
    code = main(list(argv), env or {}, out, err)
    return code, out.getvalue(), err.getvalue()


def typed(tmp_path, text):
    path = tmp_path / 'app.ini'
    path.write_text(text, encoding='utf-8')
    code, out, err = run('dump', '--format', 'json', '--config', str(path))
    assert code == 0, err
    return json.loads(out)


def test_defaults_are_milliseconds():
    code, out, _ = run('dump', '--format', 'json')
    data = json.loads(out)
    assert data['server.timeout'] == 30000
    assert data['pool.idle_timeout'] == 300000


def test_units_become_whole_milliseconds(tmp_path):
    for raw, expected in [('1.5s', 1500), ('250ms', 250), ('2', 2000), ('1m', 60000), ('1.25s', 1250)]:
        value = typed(tmp_path, f'[pool]\nidle_timeout = {raw}\n')['pool.idle_timeout']
        assert value == expected, raw
        assert isinstance(value, int) and not isinstance(value, bool), raw


def test_long_durations(tmp_path):
    assert typed(tmp_path, '[pool]\nidle_timeout = 1d\n')['pool.idle_timeout'] == 86400000
    assert typed(tmp_path, '[pool]\nidle_timeout = 0s\n')['pool.idle_timeout'] == 0
