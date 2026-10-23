import io
import json
import re

from layercfg.cli import main

CONFIG = """\
[server]
host = 0.0.0.0
port = 9000
timeout = 1.5s
allowed_hosts = a.example, b.example

[pool]
min_size = 2
idle_timeout = 90m

[cache]
max_bytes = 3kb
evict_ratio = 0.5

[log]
verbosity = warning

[app]
debug = on
"""


def run(*argv, env=None):
    out, err = io.StringIO(), io.StringIO()
    code = main(list(argv), env or {}, out, err)
    return code, out.getvalue(), err.getvalue()


def write(tmp_path, text, name):
    path = tmp_path / name
    path.write_text(text, encoding='utf-8')
    return str(path)


def test_ini_dump_loads_back_to_the_same_configuration(tmp_path):
    first = write(tmp_path, CONFIG, 'first.ini')
    code, dumped, err = run('dump', '--config', first)
    assert code == 0, err
    second = write(tmp_path, dumped, 'second.ini')
    assert run('dump', '--config', second) == (0, dumped, '')
    code, as_json, _ = run('dump', '--format', 'json', '--config', first)
    assert code == 0
    assert run('dump', '--format', 'json', '--config', second) == (0, as_json, '')
    assert json.loads(as_json)['pool.min_size'] == 2


def test_defaults_dump_loads_back(tmp_path):
    code, dumped, _ = run('dump')
    assert code == 0
    again = write(tmp_path, dumped, 'defaults.ini')
    assert run('dump', '--config', again) == (0, dumped, '')


def test_explain_names_an_environment_variable_that_works():
    for key, raw in [('server.port', '9100'), ('pool.max_size', '7'), ('log.file', '/var/log/app.log'),
                     ('server.listen_port', '9200')]:
        code, out, _ = run('explain', key)
        assert code == 0
        name = re.search(r'^\s*env:\s*(\S+)\s*$', out, re.M).group(1)
        code, value, err = run('get', key, env={name: raw})
        assert (code, value) == (0, raw + '\n'), (key, name, err)
