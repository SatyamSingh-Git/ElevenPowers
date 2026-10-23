import io

from layercfg.cli import main


def run(*argv, env=None):
    out, err = io.StringIO(), io.StringIO()
    code = main(list(argv), env or {}, out, err)
    return code, out.getvalue(), err.getvalue()


def test_single_underscore_sets_options():
    env = {'LAYERCFG_SERVER_PORT': '9001', 'LAYERCFG_POOL_MAX_SIZE': '7', 'LAYERCFG_LOG_LEVEL': 'debug',
           'LAYERCFG_SERVER_TLS_CERT': '/etc/cert.pem', 'LAYERCFG_SERVER_TLS_KEY': '/etc/key.pem'}
    assert run('get', 'server.port', env=env) == (0, '9001\n', '')
    assert run('get', 'pool.max_size', env=env) == (0, '7\n', '')
    assert run('get', 'log.level', env=env) == (0, 'debug\n', '')
    assert run('get', 'server.tls_cert', env=env) == (0, '/etc/cert.pem\n', '')


def test_aliases_have_variables_too():
    assert run('get', 'server.port', env={'LAYERCFG_SERVER_LISTEN_PORT': '9002'}) == (0, '9002\n', '')
    assert run('get', 'app.debug', env={'LAYERCFG_APP_DEV_MODE': 'on'}) == (0, 'true\n', '')


def test_environment_beats_the_file(tmp_path):
    path = tmp_path / 'app.ini'
    path.write_text('[server]\nport = 9000\nhost = 10.0.0.1\n', encoding='utf-8')
    env = {'LAYERCFG_SERVER_PORT': '9003'}
    assert run('get', 'server.port', '--config', str(path), env=env) == (0, '9003\n', '')
    assert run('get', 'server.host', '--config', str(path), env=env) == (0, '10.0.0.1\n', '')
    code, out, _ = run('dump', '--format', 'sources', '--config', str(path), env=env)
    assert '(env LAYERCFG_SERVER_PORT)' in out


def test_other_variables_are_ignored():
    assert run('check', env={'PATH': '/bin', 'HOME': '/root', 'LAYERCFGX': '1'})[:2] == (0, 'ok\n')
