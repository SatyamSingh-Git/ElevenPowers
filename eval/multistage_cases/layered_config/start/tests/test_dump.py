import json

from layercfg import APP_SCHEMA, load
from layercfg.dump import explain, format_value, render_ini, render_json, render_sources

FILE = '[server]\ntimeout = 90s\nallowed_hosts = a, b\n[cache]\nmax_bytes = 2048kb\n[db]\npassword = hunter2\n'


def test_values_are_written_in_the_largest_exact_unit():
    config = load(FILE)
    timeout, size = APP_SCHEMA.resolve('server.timeout'), APP_SCHEMA.resolve('cache.max_bytes')
    assert format_value(timeout, config['server.timeout']) == '90s'
    assert format_value(timeout, 0.25) == '250ms'
    assert format_value(timeout, 0.0) == '0ms'
    assert format_value(APP_SCHEMA.resolve('pool.idle_timeout'), 7200.0) == '2h'
    assert format_value(size, config['cache.max_bytes']) == '2mb'


def test_ini_view_loads_back_to_the_same_values():
    config = load(FILE)
    again = load(render_ini(config, reveal=True))
    assert again.as_dict() == config.as_dict()


def test_secrets_are_masked_unless_revealed():
    config = load(FILE)
    assert 'password = ***' in render_ini(config)
    assert json.loads(render_json(config))['db.password'] == '***'
    assert 'hunter2' not in render_sources(config)
    assert 'password = hunter2' in render_ini(config, reveal=True)


def test_unset_options_are_commented_out():
    assert '; tls_cert =' in render_ini(load())


def test_sources_view_names_each_layer():
    lines = render_sources(load(FILE, {'LAYERCFG_SERVER__PORT': '1'})).splitlines()
    assert lines[0].endswith('(default)')
    assert lines[1].startswith('server.port = 1 ') and lines[1].endswith('(env LAYERCFG_SERVER__PORT)')
    assert lines[2].endswith('(config.ini line 2)')


def test_explain_shows_how_to_set_an_option():
    text = explain(load(), APP_SCHEMA.resolve('log.verbosity'))
    assert text.splitlines()[0] == 'log.level = info'
    assert '  env: LAYERCFG_LOG__LEVEL' in text
    assert '  aliases: log.verbosity' in text
    assert '  choices: debug, info, warning, error' in text
