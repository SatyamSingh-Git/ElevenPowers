import io

from layercfg.cli import main

CONFIG = """\
[server]
host = 0.0.0.0
port = 9000
timeout = 45s
allowed_hosts = a.example, b.example

[pool]
max_size = 20
idle_timeout = 2h

[cache]
max_bytes = 128mb

[app]
debug = yes

[db]
password = hunter2
"""


def run(*argv, env=None):
    out, err = io.StringIO(), io.StringIO()
    code = main(list(argv), env or {}, out, err)
    return code, out.getvalue(), err.getvalue()


def write(tmp_path, text, name='app.ini'):
    path = tmp_path / name
    path.write_text(text, encoding='utf-8')
    return str(path)


def test_get_prints_values_as_a_file_would_write_them(tmp_path):
    path = write(tmp_path, CONFIG)
    expected = {
        'server.port': '9000',
        'server.host': '0.0.0.0',
        'server.timeout': '45s',
        'pool.idle_timeout': '2h',
        'cache.max_bytes': '128mb',
        'app.debug': 'true',
        'server.allowed_hosts': 'a.example, b.example',
        'pool.min_size': '1',
        'pool.max_size': '20',
    }
    for key, text in expected.items():
        assert run('get', key, '--config', path) == (0, text + '\n', ''), key


def test_get_accepts_aliases(tmp_path):
    path = write(tmp_path, CONFIG)
    assert run('get', 'server.listen_port', '--config', path)[:2] == (0, '9000\n')
    assert run('get', 'app.dev_mode', '--config', path)[:2] == (0, 'true\n')


def test_get_unset_option_prints_empty_value(tmp_path):
    path = write(tmp_path, CONFIG)
    assert run('get', 'log.file', '--config', path) == (0, '\n', '')


def test_get_unknown_key_is_a_usage_error(tmp_path):
    path = write(tmp_path, CONFIG)
    code, out, err = run('get', 'server.nope', '--config', path)
    assert code == 2
    assert out == ''
    assert "unknown key 'server.nope'" in err


def test_dump_masks_secrets(tmp_path):
    path = write(tmp_path, CONFIG)
    code, out, _ = run('dump', '--config', path)
    assert code == 0
    assert 'password = ***' in out
    assert 'hunter2' not in out
    assert 'timeout = 45s' in out


def test_check(tmp_path):
    assert run('check', '--config', write(tmp_path, CONFIG))[:2] == (0, 'ok\n')
    bad = write(tmp_path, '[server]\nport = abc\n[pool]\nmax_size = 5000\n[log]\nlevel = loud\n', 'bad.ini')
    code, _, err = run('check', '--config', bad)
    assert code == 1
    assert "bad.ini line 2: server.port: expected int, got 'abc'" in err
    assert 'bad.ini line 4: pool.max_size: must be at most 1000' in err
    assert 'bad.ini line 6: log.level: must be one of debug, info, warning, error' in err
