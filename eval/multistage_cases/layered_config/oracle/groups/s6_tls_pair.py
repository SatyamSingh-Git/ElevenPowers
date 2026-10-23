import io

import pytest

from layercfg import ValidationError, load
from layercfg.cli import main

MESSAGE = 'server.tls_cert and server.tls_key must be set together'


def run(*argv, env=None):
    out, err = io.StringIO(), io.StringIO()
    code = main(list(argv), env or {}, out, err)
    return code, out.getvalue(), err.getvalue()


def test_certificate_without_key(tmp_path):
    path = tmp_path / 'app.ini'
    path.write_text('[server]\ntls_cert = /etc/cert.pem\n', encoding='utf-8')
    code, _, err = run('check', '--config', str(path))
    assert code == 1
    assert f'app.ini line 2: {MESSAGE}' in err


def test_key_without_certificate():
    with pytest.raises(ValidationError) as caught:
        load(env={'LAYERCFG_SERVER_TLS_KEY': '/etc/key.pem'})
    assert str(caught.value) == f'env LAYERCFG_SERVER_TLS_KEY: {MESSAGE}'


def test_both_or_neither_is_fine():
    config = load(files=[('app.ini', '[server]\ntls_cert = /etc/cert.pem\n')],
                  env={'LAYERCFG_SERVER_TLS_KEY': '/etc/key.pem'})
    assert config['server.tls_cert'] == '/etc/cert.pem'
    assert load()['server.tls_cert'] is None
