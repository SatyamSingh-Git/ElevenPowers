from layercfg import load

SITE = ('site.ini', '[server]\nport = 9000\nhost = 10.0.0.1\n\n[pool]\nmax_size = 4\n')
HOST = ('host.ini', '[server]\nhost = 10.0.0.2\n[log]\nlevel = debug\n')


def test_later_files_override_earlier_ones():
    config = load(files=[SITE, HOST])
    assert config['server.port'] == 9000
    assert config['server.host'] == '10.0.0.2'
    assert config['pool.max_size'] == 4
    assert config['log.level'] == 'debug'
    assert load(files=[HOST, SITE])['server.host'] == '10.0.0.1'


def test_sources_name_the_file():
    config = load(files=[SITE, HOST])
    assert config.source('server.port') == 'site.ini line 2'
    assert config.source('server.host') == 'host.ini line 2'
    assert config.source('pool.max_size') == 'site.ini line 6'
    assert config.source('pool.min_size') == 'default'


def test_environment_still_wins():
    config = load(files=[SITE, HOST], env={'LAYERCFG_SERVER_HOST': '10.0.0.3'})
    assert config['server.host'] == '10.0.0.3'
    assert config.source('server.host') == 'env LAYERCFG_SERVER_HOST'


def test_no_files_means_defaults():
    assert load(files=[])['server.port'] == 8080
    assert load(files=[], env={'LAYERCFG_SERVER_PORT': '1'})['server.port'] == 1
