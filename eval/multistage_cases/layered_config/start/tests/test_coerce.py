import pytest

from layercfg import APP_SCHEMA, CoercionError
from layercfg.coerce import check_range, coerce


def option(key):
    return APP_SCHEMA.resolve(key)


@pytest.mark.parametrize('key, raw, expected', [
    ('server.port', ' 9000 ', 9000),
    ('cache.evict_ratio', '0.5', 0.5),
    ('app.debug', 'yes', True),
    ('app.debug', 'off', False),
    ('app.debug', '1', True),
    ('server.host', '  0.0.0.0 ', '0.0.0.0'),
    ('server.allowed_hosts', 'a, b,,c ', ['a', 'b', 'c']),
    ('server.allowed_hosts', '', []),
    ('cache.max_bytes', '64mb', 64 * 1024 * 1024),
    ('cache.max_bytes', '512', 512),
    ('cache.max_bytes', '2 KB', 2048),
    ('log.level', 'debug', 'debug'),
])
def test_coerces_each_type(key, raw, expected):
    assert coerce(option(key), raw) == expected


@pytest.mark.parametrize('raw, seconds', [
    ('30s', 30.0),
    ('1.5s', 1.5),
    ('250ms', 0.25),
    ('2', 2.0),
    ('5m', 300.0),
    ('1h', 3600.0),
])
def test_durations_are_seconds(raw, seconds):
    assert coerce(option('server.timeout'), raw) == seconds


@pytest.mark.parametrize('key, raw, message', [
    ('server.port', 'abc', "expected int, got 'abc'"),
    ('cache.evict_ratio', 'nan', "expected float, got 'nan'"),
    ('app.debug', 'maybe', "expected bool, got 'maybe'"),
    ('server.timeout', '10 parsecs', "expected duration, got '10 parsecs'"),
    ('cache.max_bytes', '1.5mb', "expected size, got '1.5mb'"),
    ('log.level', 'loud', 'must be one of debug, info, warning, error'),
])
def test_bad_values_say_what_was_expected(key, raw, message):
    with pytest.raises(CoercionError) as caught:
        coerce(option(key), raw)
    assert str(caught.value) == message


def test_range_is_checked_in_the_option_unit():
    assert check_range(option('server.port'), 0) == 'must be at least 1'
    assert check_range(option('server.port'), 70000) == 'must be at most 65535'
    assert check_range(option('server.timeout'), 601.0) == 'must be at most 10m'
    assert check_range(option('server.timeout'), 600.0) is None
    assert check_range(option('server.host'), 'x') is None
