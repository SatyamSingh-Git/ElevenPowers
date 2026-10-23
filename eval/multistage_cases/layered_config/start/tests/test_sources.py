import pytest

from layercfg import ParseError
from layercfg.envsource import read_env
from layercfg.iniparse import parse


def test_sections_dot_their_keys():
    entries = parse('[Server]\nPort = 9000\n\n# note\n; other\n[pool]\nmax-size=4\n', 'app.ini')
    assert [(e.key, e.raw, e.source) for e in entries] == [
        ('server.port', '9000', 'app.ini line 2'),
        ('pool.max_size', '4', 'app.ini line 7'),
    ]


def test_indented_lines_continue_a_value():
    entries = parse('[server]\nallowed_hosts = a,\n    b,\n\n  c\nport = 1\n', 'app.ini')
    assert entries[0].raw == 'a, b, c'
    assert entries[0].source == 'app.ini line 2'
    assert entries[1].key == 'server.port'


def test_byte_order_mark_is_ignored():
    assert parse('﻿[server]\nport = 1\n', 'app.ini')[0].key == 'server.port'


@pytest.mark.parametrize('text, message', [
    ('[server]\njust words\n', "app.ini line 2: expected 'key = value' or '[section]'"),
    ('port = 1\n', 'app.ini line 1: key outside of a section'),
    ('[a..b]\n', "app.ini line 1: bad section name 'a..b'"),
])
def test_syntax_errors_name_the_line(text, message):
    with pytest.raises(ParseError) as caught:
        parse(text, 'app.ini')
    assert str(caught.value) == message


def test_env_variables_map_to_dotted_keys():
    env = {'LAYERCFG_SERVER__PORT': '1', 'LAYERCFG_POOL__MAX_SIZE': '2', 'PATH': '/bin', 'LAYERCFG_': 'x'}
    entries = read_env(env)
    assert [(e.key, e.raw, e.source, e.layer) for e in entries] == [
        ('pool.max_size', '2', 'env LAYERCFG_POOL__MAX_SIZE', 'env'),
        ('server.port', '1', 'env LAYERCFG_SERVER__PORT', 'env'),
    ]


def test_env_prefix_can_be_changed():
    assert [e.key for e in read_env({'MYAPP_LOG__LEVEL': 'debug', 'LAYERCFG_LOG__LEVEL': 'x'}, 'MYAPP_')] == ['log.level']
