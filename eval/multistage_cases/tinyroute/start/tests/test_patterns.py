import pytest

from tinyroute import BuildError, RouteError, register_converter
from tinyroute.converters import Converter
from tinyroute.patterns import Pattern


def test_literal_pattern_matches_only_itself():
    pattern = Pattern('/about')
    assert pattern.match('/about') == {}
    assert pattern.match('/about/') is None
    assert pattern.match('/abou') is None


def test_untyped_parameter_is_a_string_without_slashes():
    pattern = Pattern('/users/<name>')
    assert pattern.match('/users/ada') == {'name': 'ada'}
    assert pattern.match('/users/ada/posts') is None


def test_int_parameter_is_converted():
    assert Pattern('/users/<int:id>').match('/users/42') == {'id': 42}
    assert Pattern('/users/<int:id>').match('/users/-1') is None


def test_slug_and_path_parameters():
    assert Pattern('/posts/<slug:slug>').match('/posts/hello-world') == {'slug': 'hello-world'}
    assert Pattern('/posts/<slug:slug>').match('/posts/Hello') is None
    assert Pattern('/files/<path:name>').match('/files/a/b.txt') == {'name': 'a/b.txt'}


def test_parameters_are_percent_decoded():
    assert Pattern('/files/<name>').match('/files/a%20b') == {'name': 'a b'}


def test_parameter_inside_a_segment():
    assert Pattern('/v<int:major>/status').match('/v2/status') == {'major': 2}


@pytest.mark.parametrize('text', ['users', '/users/<int:id', '/a/<x>/<x>', '/a/<nope:x>'])
def test_bad_patterns_are_refused(text):
    with pytest.raises(RouteError):
        Pattern(text)


def test_unknown_type_message():
    with pytest.raises(RouteError, match="unknown parameter type 'nope'"):
        Pattern('/a/<nope:x>')


def test_build_round_trips():
    pattern = Pattern('/users/<int:id>/files/<path:name>')
    assert pattern.build({'id': 3, 'name': 'a b/c.txt'}, 'f') == '/users/3/files/a%20b/c.txt'


def test_build_refuses_values_the_type_would_not_match():
    with pytest.raises(BuildError, match="invalid value 'x' for parameter 'id' of route 'u'"):
        Pattern('/users/<int:id>').build({'id': 'x'}, 'u')
    with pytest.raises(BuildError):
        Pattern('/users/<int:id>').build({'id': True}, 'u')


def test_build_reports_missing_parameter():
    with pytest.raises(BuildError, match="missing parameter 'id' for route 'u'"):
        Pattern('/users/<int:id>').build({}, 'u')


def test_registered_converter_is_usable():
    class Upper(Converter):
        regex = '[A-Z]+'

    register_converter('upper', Upper())
    assert Pattern('/codes/<upper:code>').match('/codes/ABC') == {'code': 'ABC'}
    with pytest.raises(RouteError):
        register_converter('Bad-Name', Upper())
