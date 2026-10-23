import pytest

from layercfg import ParseError, ValidationError, load


def test_problems_from_every_file_are_reported_together():
    first = ('a.ini', '[server]\nport = abc\n')
    second = ('b.ini', '[pool]\nmax_size = 5000\nnope = 1\n')
    with pytest.raises(ValidationError) as caught:
        load(files=[first, second], env={'LAYERCFG_LOG_LEVEL': 'loud'})
    lines = str(caught.value).splitlines()
    assert "a.ini line 2: server.port: expected int, got 'abc'" in lines
    assert 'b.ini line 2: pool.max_size: must be at most 1000' in lines
    assert "b.ini line 3: unknown key 'pool.nope'" in lines
    assert 'env LAYERCFG_LOG_LEVEL: log.level: must be one of debug, info, warning, error' in lines


def test_a_bad_value_in_a_later_file_is_named_by_that_file():
    with pytest.raises(ValidationError) as caught:
        load(files=[('a.ini', '[server]\nport = 1\n'), ('b.ini', '\n[server]\nport = 0\n')])
    assert str(caught.value) == 'b.ini line 3: server.port: must be at least 1'


def test_syntax_error_names_its_file():
    with pytest.raises(ParseError) as caught:
        load(files=[('a.ini', '[server]\nport = 1\n'), ('b.ini', 'port = 1\n')])
    assert str(caught.value) == 'b.ini line 1: key outside of a section'
