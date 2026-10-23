from layercfg import load


def test_default_stands_in_for_an_unset_option():
    config = load(files=[])
    assert config.get('log.file', 'stderr') == 'stderr'
    assert config.get('db.password', '') == ''
    assert config.get('log.file') is None


def test_default_is_ignored_when_the_option_has_a_value():
    config = load(files=[], env={'LAYERCFG_LOG_FILE': '/var/log/app.log'})
    assert config.get('log.file', 'stderr') == '/var/log/app.log'
    assert config.get('server.port', 1) == 8080
    assert config.get('app.debug', True) is False
