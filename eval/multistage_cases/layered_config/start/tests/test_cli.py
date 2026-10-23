import io
import json

from layercfg.cli import main


def run(*argv, env=None):
    out, err = io.StringIO(), io.StringIO()
    code = main(list(argv), env, out, err)
    return code, out.getvalue(), err.getvalue()


def write(tmp_path, text, name='app.ini'):
    path = tmp_path / name
    path.write_text(text, encoding='utf-8')
    return str(path)


def test_get_prints_the_value(tmp_path):
    path = write(tmp_path, '[server]\ntimeout = 2m\n[db]\npassword = pw\n')
    assert run('get', 'server.timeout', '--config', path) == (0, '2m\n', '')
    assert run('get', 'server.timeout', '--json', '--config', path) == (0, '120.0\n', '')
    assert run('get', 'db.password', '--config', path) == (0, '***\n', '')
    assert run('get', 'db.password', '--reveal', '--config', path) == (0, 'pw\n', '')
    assert run('get', 'log.file') == (0, '\n', '')


def test_get_unknown_key_is_a_usage_error():
    code, out, err = run('get', 'server.nope')
    assert (code, out) == (2, '')
    assert err == "unknown key 'server.nope'\n"


def test_check_reports_problems(tmp_path):
    path = write(tmp_path, '[server]\nport = abc\n')
    code, out, err = run('check', '--config', path)
    assert code == 1
    assert "app.ini line 2: server.port: expected int, got 'abc'" in err
    assert run('check')[:2] == (0, 'ok\n')


def test_env_is_layered(tmp_path):
    assert run('get', 'server.port', env={'LAYERCFG_SERVER__PORT': '9'})[1] == '9\n'
    assert run('get', 'server.port', '--env-prefix', 'X_', env={'X_SERVER__PORT': '8'})[1] == '8\n'


def test_dump_formats(tmp_path):
    path = write(tmp_path, '[pool]\nmax_size = 3\n')
    assert json.loads(run('dump', '--format', 'json', '--config', path)[1])['pool.max_size'] == 3
    assert '[pool]\nmin_size = 1\nmax_size = 3\n' in run('dump', '--config', path)[1]


def test_unreadable_file_and_bad_usage(tmp_path):
    code, _, err = run('check', '--config', str(tmp_path / 'missing.ini'))
    assert code == 2 and err.startswith('cannot read ')
    assert run('frobnicate')[0] == 2


def test_explain_and_keys():
    assert '  env: LAYERCFG_SERVER__PORT' in run('explain', 'server.listen_port')[1]
    assert run('explain', 'nope.nope')[0] == 2
    assert run('keys')[1].splitlines()[0] == 'server.host  (str)  Address to listen on.'
    assert run('version') == (0, '1.4.0\n', '')
