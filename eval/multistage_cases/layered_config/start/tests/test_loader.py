import pytest

from layercfg import Option, Schema, ValidationError, load

FILE = '[server]\nport = 9000\nhost = 0.0.0.0\n[log]\nverbosity = debug\n'


def test_defaults_alone():
    config = load()
    assert config['server.port'] == 8080
    assert config['server.timeout'] == 30.0
    assert config['log.file'] is None
    assert config.source('server.port') == 'default'


def test_env_beats_file_beats_defaults():
    config = load(FILE, {'LAYERCFG_SERVER__PORT': '9100'}, file_name='app.ini')
    assert config['server.port'] == 9100
    assert config.source('server.port') == 'env LAYERCFG_SERVER__PORT'
    assert config['server.host'] == '0.0.0.0'
    assert config.source('server.host') == 'app.ini line 3'
    assert config['pool.max_size'] == 10


def test_aliases_set_and_read_the_same_option():
    config = load(FILE)
    assert config['log.level'] == 'debug'
    assert config['log.verbosity'] == 'debug'
    assert config.source('log.verbosity') == 'config.ini line 5'


def test_get_returns_the_default_for_unknown_keys():
    config = load()
    assert config.get('server.port') == 8080
    assert config.get('server.nope') is None
    assert config.get('server.nope', 7) == 7
    with pytest.raises(KeyError):
        config['server.nope']


def test_every_problem_is_reported_together():
    text = '[server]\nport = abc\nsurprise = 1\n[pool]\nmax_size = 5000\n'
    with pytest.raises(ValidationError) as caught:
        load(text, {'LAYERCFG_LOG__LEVEL': 'loud', 'LAYERCFG_NOPE': '1'}, file_name='app.ini')
    assert [str(issue) for issue in caught.value.issues] == [
        "app.ini line 2: server.port: expected int, got 'abc'",
        "app.ini line 3: unknown key 'server.surprise'",
        'app.ini line 5: pool.max_size: must be at most 1000',
        'env LAYERCFG_LOG__LEVEL: log.level: must be one of debug, info, warning, error',
        'env LAYERCFG_NOPE: unknown variable',
    ]


def test_defaults_are_not_a_floor_for_ranges():
    with pytest.raises(ValidationError):
        load('[server]\nport = 0\n')
    assert load('[pool]\nmin_size = 0\n')['pool.min_size'] == 0


def test_custom_schema_and_prefix():
    schema = Schema([Option('job.retries', 'int', '3', aliases=('job.attempts',))])
    config = load('[job]\nattempts = 5\n', {'JOBS_JOB__RETRIES': '6'}, schema=schema, env_prefix='JOBS_')
    assert config.as_dict() == {'job.retries': 6}


def test_schema_refuses_clashing_names():
    with pytest.raises(ValueError):
        Schema([Option('a.b', 'int', '1'), Option('a.c', 'int', '1', aliases=('a.b',))])
    with pytest.raises(ValueError):
        Schema([Option('A.b', 'int', '1')])
