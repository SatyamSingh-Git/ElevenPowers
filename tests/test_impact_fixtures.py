"""Source-only pytest fixture relationships match independently executed scopes."""
import os
import subprocess
import sys

import pytest

from core.impact import build, analyze


def put(root, path, source):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding='utf-8')


def sample(root):
    put(root, 'api.py', 'class Api: pass\n')
    put(root, 'tests/conftest.py', 'import pytest\nfrom api import Api\n@pytest.fixture\ndef env(): return Api()\n')


def dependencies(value):
    definitions = {e.source: e.target for e in value.edges if e.kind == 'fixture_definition'}
    return {(definitions.get(e.source, e.source), definitions.get(e.target, e.target))
            for e in value.edges if e.kind == 'fixture'}


def test_ancestor_fixture_connects_test_to_qualified_factory(tmp_path):
    sample(tmp_path)
    put(tmp_path, 'tests/test_api.py', 'def test_api(env): assert env\n')
    value = build(tmp_path)
    assert ('symbol:tests/test_api.py#test_api', 'symbol:tests/conftest.py#env') in dependencies(value)
    report = analyze(value, ['symbol:api.py#Api'])
    assert 'tests/test_api.py' in {n['path'] for n in report['tests']}
    witness = next(n for n in report['tests'] if n['path']=='tests/test_api.py')['explanation']
    assert any(e['kind'] == 'fixture' and e['origin'] == 'static' for e in witness)


def test_fixture_dependencies_and_class_method_requests_keep_the_chain(tmp_path):
    sample(tmp_path)
    put(tmp_path, 'tests/conftest.py', (tmp_path/'tests/conftest.py').read_text()+
        '@pytest.fixture\ndef client(env): return env\n')
    put(tmp_path, 'tests/test_api.py', 'class TestApi:\n    def test_api(self, client): assert client\n')
    value = build(tmp_path)
    edges = dependencies(value)
    assert ('symbol:tests/conftest.py#client', 'symbol:tests/conftest.py#env') in edges
    assert ('symbol:tests/test_api.py#TestApi.test_api', 'symbol:tests/conftest.py#client') in edges


def test_local_override_does_not_choose_same_named_ancestor(tmp_path):
    sample(tmp_path)
    put(tmp_path, 'tests/test_api.py', 'import pytest\n@pytest.fixture\ndef env(): return 2\ndef test_api(env): assert env==2\n')
    edges = dependencies(build(tmp_path))
    assert ('symbol:tests/test_api.py#test_api', 'symbol:tests/test_api.py#env') in edges
    assert ('symbol:tests/test_api.py#test_api', 'symbol:tests/conftest.py#env') not in edges


def test_override_can_request_outer_fixture_with_the_same_name(tmp_path):
    sample(tmp_path)
    put(tmp_path, 'tests/test_api.py', 'import pytest\n@pytest.fixture\ndef env(env): return env\ndef test_api(env): assert env\n')
    edges = dependencies(build(tmp_path))
    assert ('symbol:tests/test_api.py#env', 'symbol:tests/conftest.py#env') in edges


@pytest.mark.parametrize('mark,focused', [
    ('pytest.mark.parametrize("env", ["direct"])', False),
    ('pytest.mark.usefixtures("env")', True),
])
def test_class_assigned_marks_match_direct_values_and_fixture_requests(tmp_path, mark, focused):
    sample(tmp_path)
    argument = ', env' if not focused else ''
    put(tmp_path, 'tests/test_api.py', f'import pytest\nclass TestApi:\n    pytestmark={mark}\n'
        f'    def test_api(self{argument}): assert True\n')
    report = analyze(build(tmp_path), ['symbol:api.py#Api'], max_depth=20)
    assert bool(report['test_selection']['focused']) is focused


def test_rebound_class_marks_leave_the_context_unresolved(tmp_path):
    sample(tmp_path)
    put(tmp_path, 'tests/test_api.py', 'import pytest\nclass TestApi:\n'
        '    pytestmark=pytest.mark.usefixtures("env")\n    pytestmark=[]\n'
        '    def test_api(self, env): assert True\n')
    report=analyze(build(tmp_path), ['symbol:api.py#Api'])
    assert not report['test_selection']['focused']
    assert not report['coverage']['complete']


@pytest.mark.parametrize('imports', ['from fixtures import *', 'from helper import exported'])
def test_wildcard_and_reexported_fixtures_cannot_fall_through_to_ancestor(tmp_path, imports):
    sample(tmp_path)
    put(tmp_path, 'fixtures.py', 'import pytest\n@pytest.fixture\ndef env(): return "other"\n')
    put(tmp_path, 'helper.py', 'from fixtures import env as exported\n')
    put(tmp_path, 'tests/test_api.py', imports+'\ndef test_api(env): assert env=="other"\n')
    report=analyze(build(tmp_path), ['symbol:api.py#Api'])
    assert not report['test_selection']['focused']
    assert not report['coverage']['complete']


def test_indirect_override_chain_requests_the_active_outer_definition(tmp_path):
    sample(tmp_path)
    put(tmp_path, 'tests/test_api.py', 'import pytest\n@pytest.fixture\ndef env(other): return other\n'
        '@pytest.fixture\ndef other(env): return env\ndef test_api(env): assert env\n')
    graph=build(tmp_path)
    assert ('symbol:tests/test_api.py#other', 'symbol:tests/conftest.py#env') in dependencies(graph)
    assert not any('cyclic pytest fixture' in issue for issue in graph.issues)
    assert analyze(graph, ['symbol:api.py#Api'], max_depth=20)['test_selection']['focused']


def test_sibling_conftest_fixture_is_not_visible(tmp_path):
    put(tmp_path, 'tests/unit/conftest.py', 'import pytest\n@pytest.fixture\ndef env(): return 1\n')
    put(tmp_path, 'tests/integration/test_api.py', 'def test_api(env): assert env\n')
    value = build(tmp_path)
    assert not dependencies(value)
    assert any('unresolved pytest fixture' in issue for issue in value.issues)


@pytest.mark.parametrize('decorator', ['@pytest.fixture', '@pytest.fixture()', '@pytest.fixture(name="env")'])
def test_proven_fixture_alias_and_literal_registration_name(tmp_path, decorator):
    source = 'import pytest as p\n' + decorator.replace('pytest.', 'p.')+'\ndef env(): return 1\n'
    put(tmp_path, 'conftest.py', source)
    put(tmp_path, 'test_api.py', 'def test_api(env): assert env\n')
    assert dependencies(build(tmp_path))


def test_autouse_and_literal_usefixtures_marks_are_dependencies(tmp_path):
    put(tmp_path, 'conftest.py', 'from pytest import fixture\n@fixture(autouse=True)\ndef ready(): pass\n'
        '@fixture\ndef env(): return 1\n')
    put(tmp_path, 'test_api.py', 'import pytest\n@pytest.mark.usefixtures("env")\ndef test_api(): assert True\n')
    edges = dependencies(build(tmp_path))
    assert ('symbol:test_api.py#test_api', 'symbol:conftest.py#ready') in edges
    assert ('symbol:test_api.py#test_api', 'symbol:conftest.py#env') in edges


@pytest.mark.parametrize('indirect,expected', [('', False), (', indirect=True', True), (', indirect=["env"]', True)])
def test_direct_parameter_values_are_not_mislabelled_as_fixtures(tmp_path, indirect, expected):
    sample(tmp_path)
    put(tmp_path, 'tests/test_api.py', 'import pytest\n@pytest.mark.parametrize("env",[1]'+indirect+')\n'
        'def test_api(env): assert env\n')
    edge = ('symbol:tests/test_api.py#test_api', 'symbol:tests/conftest.py#env')
    assert (edge in dependencies(build(tmp_path))) is expected


def test_module_and_class_usefixtures_marks_are_inherited(tmp_path):
    sample(tmp_path)
    put(tmp_path, 'tests/test_api.py', 'import pytest\npytestmark=pytest.mark.usefixtures("env")\n'
        '@pytest.mark.usefixtures("env")\nclass TestApi:\n    def test_api(self): assert True\n')
    assert ('symbol:tests/test_api.py#TestApi.test_api', 'symbol:tests/conftest.py#env') in dependencies(build(tmp_path))


@pytest.mark.parametrize('declaration', [
    '@pytest.fixture(name=dynamic)\ndef env(): pass\n',
    '@pytest.fixture\ndef env(): pass\nenv=lambda:2\n',
    '@pytest.fixture(autouse=dynamic)\ndef env(): pass\n',
])
def test_dynamic_or_rebound_fixture_registration_is_explicitly_incomplete(tmp_path, declaration):
    put(tmp_path, 'conftest.py', 'import pytest\n'+declaration)
    put(tmp_path, 'test_api.py', 'def test_api(env): assert env\n')
    value = build(tmp_path)
    assert not dependencies(value)
    assert any('pytest fixture' in issue for issue in value.issues)


def test_local_pytest_module_cannot_create_proven_framework_fixtures(tmp_path):
    put(tmp_path, 'pytest.py', 'def fixture(fn): return fn\n')
    put(tmp_path, 'conftest.py', 'import pytest\n@pytest.fixture\ndef env(): return 1\n')
    put(tmp_path, 'test_api.py', 'def test_api(env): assert env\n')
    value = build(tmp_path)
    assert not dependencies(value)
    assert any('pytest fixture' in issue for issue in value.issues)


def test_unsupported_class_fixture_override_does_not_fall_back_to_ancestor(tmp_path):
    sample(tmp_path)
    put(tmp_path, 'tests/test_api.py', 'import pytest\nclass TestApi:\n'
        '    @pytest.fixture\n    def env(self): return 2\n'
        '    def test_api(self, env): assert env==2\n')
    value = build(tmp_path)
    assert ('symbol:tests/test_api.py#TestApi.test_api', 'symbol:tests/conftest.py#env') not in dependencies(value)
    assert any('class pytest fixture' in issue for issue in value.issues)


def test_actual_pytest_producer_agrees_with_outer_override_and_direct_parameter(tmp_path):
    put(tmp_path, 'conftest.py', 'import pytest\n@pytest.fixture\ndef env(): return "A"\n')
    put(tmp_path, 'test_api.py', 'import pytest\n@pytest.fixture\ndef env(env): return env+"B"\n'
        'def test_override(env): assert env=="AB"\n'
        '@pytest.mark.parametrize("env",["direct"])\ndef test_direct(env): assert env=="direct"\n')
    done = subprocess.run([sys.executable, '-m', 'pytest', 'test_api.py', '-q', '-p', 'no:cacheprovider'],
        cwd=tmp_path, env={**os.environ, 'PYTHONDONTWRITEBYTECODE':'1'}, capture_output=True, text=True, timeout=30)
    assert done.returncode == 0, done.stdout+done.stderr
    assert '2 passed' in done.stdout
    edges = dependencies(build(tmp_path))
    assert ('symbol:test_api.py#env', 'symbol:conftest.py#env') in edges
    assert ('symbol:test_api.py#test_direct', 'symbol:test_api.py#env') not in edges


def test_dependency_lookup_context_cannot_leak_between_sibling_overrides(tmp_path):
    sample(tmp_path)
    put(tmp_path, 'tests/conftest.py', (tmp_path/'tests/conftest.py').read_text()+
        '@pytest.fixture\ndef client(env): return env\n')
    put(tmp_path, 'tests/a/test_api.py', 'def test_api(client): assert client\n')
    put(tmp_path, 'tests/b/test_api.py', 'import pytest\n@pytest.fixture\ndef env(): return 2\n'
        'def test_api(client): assert client==2\n')
    report = analyze(build(tmp_path), ['symbol:api.py#Api'], max_depth=20)
    tests = {n['path'] for n in report['tests']}
    assert 'tests/a/test_api.py' in tests
    assert 'tests/b/test_api.py' not in tests


def test_defaulted_function_arguments_are_not_required_fixture_requests(tmp_path):
    sample(tmp_path)
    put(tmp_path, 'tests/test_api.py', 'def test_api(env=1, *, other=2): assert env==1\n')
    assert not dependencies(build(tmp_path))


def test_duplicate_literal_registration_names_are_not_resolved_by_source_order(tmp_path):
    put(tmp_path, 'conftest.py', 'import pytest\n@pytest.fixture(name="env")\ndef first(): return 1\n'
        '@pytest.fixture(name="env")\ndef second(): return 2\n')
    put(tmp_path, 'test_api.py', 'def test_api(env): assert env\n')
    value = build(tmp_path)
    assert not dependencies(value)
    assert any('ambiguous pytest fixture' in issue for issue in value.issues)


def test_unknown_decorator_cannot_turn_direct_values_into_fixture_requests(tmp_path):
    sample(tmp_path)
    put(tmp_path, 'tests/test_api.py', '@unknown_parameter_mark\ndef test_api(env): assert env\n')
    value = build(tmp_path)
    assert not dependencies(value)
    assert any('pytest fixture request' in issue for issue in value.issues)


def test_direct_parameter_masks_an_autouse_fixture_of_the_same_name(tmp_path):
    put(tmp_path, 'conftest.py', 'import pytest\n@pytest.fixture(autouse=True)\ndef env(): return 1\n')
    put(tmp_path, 'test_api.py', 'import pytest\n@pytest.mark.parametrize("env",[2])\ndef test_api(env): assert env==2\n')
    assert not dependencies(build(tmp_path))


def test_direct_parameter_dependency_does_not_leak_to_another_test_in_the_same_file(tmp_path):
    sample(tmp_path)
    put(tmp_path, 'tests/conftest.py', (tmp_path/'tests/conftest.py').read_text()+
        '@pytest.fixture\ndef client(env): return env\n')
    put(tmp_path, 'tests/test_api.py', 'import pytest\ndef test_normal(client): assert client\n'
        '@pytest.mark.parametrize("env",[2])\ndef test_supplied(client): assert client==2\n')
    report = analyze(build(tmp_path), ['symbol:api.py#Api'], max_depth=20)
    assert any(n['id']=='symbol:tests/test_api.py#test_normal' for n in report['tests'])
    assert not any(n['id']=='symbol:tests/test_api.py#test_supplied' for n in report['tests'])


def test_rebound_test_class_does_not_register_obsolete_fixture_requests(tmp_path):
    sample(tmp_path)
    put(tmp_path, 'tests/test_api.py', 'class TestApi:\n    def test_api(self, env): assert env\nTestApi=object\n')
    value = build(tmp_path)
    assert not dependencies(value)
    assert any('pytest class' in issue for issue in value.issues)


def test_rebound_module_marks_are_explicitly_unresolved(tmp_path):
    sample(tmp_path)
    put(tmp_path, 'tests/test_api.py', 'import pytest\npytestmark=pytest.mark.usefixtures("env")\n'
        'pytestmark=pytest.mark.skip\ndef test_api(): assert True\n')
    value = build(tmp_path)
    assert not dependencies(value)
    assert any('pytest mark' in issue for issue in value.issues)


def test_usefixtures_treats_each_argument_as_one_exact_name(tmp_path):
    sample(tmp_path)
    put(tmp_path, 'tests/test_api.py', 'import pytest\n@pytest.mark.usefixtures("env,other")\n'
        'def test_api(): assert True\n')
    value = build(tmp_path)
    assert not dependencies(value)
    assert any('pytest fixture request' in issue for issue in value.issues)


def test_unsupported_positional_parametrize_options_are_not_treated_as_direct_values(tmp_path):
    sample(tmp_path)
    put(tmp_path, 'tests/test_api.py', 'import pytest\n@pytest.mark.parametrize("env",[2],True)\n'
        'def test_api(env): assert env\n')
    value = build(tmp_path)
    assert not dependencies(value)
    assert any('pytest fixture request' in issue for issue in value.issues)


@pytest.mark.parametrize('source', [
    'from fixture_library import env\ndef test_api(env): assert env\n',
    'import pytest\nenv=pytest.fixture(lambda:2)\ndef test_api(env): assert env\n',
    'import pytest\nif condition:\n    @pytest.fixture\n    def env(): return 2\ndef test_api(env): assert env\n',
])
def test_unsupported_registration_cannot_invent_an_ancestor_lookup(tmp_path, source):
    sample(tmp_path)
    put(tmp_path, 'fixture_library.py', 'import pytest\n@pytest.fixture\ndef env(): return 2\n')
    put(tmp_path, 'tests/test_api.py', source)
    value = build(tmp_path)
    assert ('symbol:tests/test_api.py#test_api', 'symbol:tests/conftest.py#env') not in dependencies(value)
    assert any('pytest fixture' in issue for issue in value.issues)


def test_assignment_alias_to_a_fixture_does_not_invent_an_ancestor_lookup(tmp_path):
    sample(tmp_path)
    put(tmp_path, 'tests/test_api.py', 'import pytest\n@pytest.fixture\ndef inner(): return 2\n'
        'env=inner\ndef test_api(env): assert env==2\n')
    value = build(tmp_path)
    assert ('symbol:tests/test_api.py#test_api', 'symbol:tests/conftest.py#env') not in dependencies(value)
    assert any('pytest fixture' in issue for issue in value.issues)
