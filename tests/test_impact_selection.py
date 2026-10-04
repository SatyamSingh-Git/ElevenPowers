"""Specific test witnesses are ranked without silently dropping broad fallbacks."""
import json

import pytest

from core.impact import build, analyze, markdown


def put(root, path, source):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding='utf-8')


def sample(root):
    put(root, 'api.py', 'def expire(): return 1\ndef other(): return 2\n')
    put(root, 'test_call.py', 'from api import expire\ndef test_call(): assert expire()==1\n')
    put(root, 'test_import.py', 'import api\ndef test_other(): assert True\n')


def paths(rows):
    return {n['path'] for n in rows}


def test_focused_call_and_broad_import_are_separate_and_both_retained(tmp_path):
    sample(tmp_path)
    report = analyze(build(tmp_path), ['symbol:api.py#expire'])
    selection = report['test_selection']
    assert paths(selection['focused']) == {'test_call.py'}
    assert paths(selection['fallback']) == {'test_import.py'}
    assert paths(report['tests']) == {'test_call.py', 'test_import.py'}
    assert selection['safe_to_exclude_fallback'] is False


def test_specific_longer_path_survives_a_shorter_broad_witness(tmp_path):
    sample(tmp_path)
    put(tmp_path, 'first.py', 'from api import expire\ndef first(): return expire()\n')
    put(tmp_path, 'second.py', 'from first import first\ndef second(): return first()\n')
    put(tmp_path, 'test_mixed.py', 'import api\nfrom second import second\ndef test_run(): assert second()==1\n')
    report = analyze(build(tmp_path), ['symbol:api.py#expire'])
    specific = next(n for n in report['test_selection']['focused'] if n['path']=='test_mixed.py')
    assert len(specific['explanation']) == 3
    assert all(e['kind'] == 'calls' for e in specific['explanation'])
    assert next(n for n in report['tests'] if n['id']=='file:test_mixed.py')['distance'] < specific['distance']


def test_fixture_specific_path_is_preferred_and_conftest_remains_support(tmp_path):
    put(tmp_path, 'api.py', 'class Api: pass\n')
    put(tmp_path, 'tests/conftest.py', 'import pytest\nfrom api import Api\n@pytest.fixture\ndef env(): return Api()\n')
    put(tmp_path, 'tests/test_api.py', 'def test_api(env): assert env\n')
    report = analyze(build(tmp_path), ['symbol:api.py#Api'], max_depth=20)
    focused = report['test_selection']['focused']
    assert paths(focused) == {'tests/test_api.py'}
    assert any(e['kind'] == 'fixture' for e in focused[0]['explanation'])
    assert 'tests/conftest.py' in paths(report['test_selection']['support'])


def test_unused_fixture_body_is_not_a_focused_test_call(tmp_path):
    put(tmp_path, 'api.py', 'def expire(): return 1\n')
    put(tmp_path, 'test_api.py', 'import pytest\nfrom api import expire\n@pytest.fixture\ndef unused(): return expire()\n'
        'def test_other(): assert True\n')
    report = analyze(build(tmp_path), ['symbol:api.py#expire'])
    assert not report['test_selection']['focused']
    assert 'test_api.py' in paths(report['test_selection']['fallback'])


def test_actual_module_call_is_a_specific_dependency_without_assertion_claim(tmp_path):
    put(tmp_path, 'api.py', 'def expire(): return 1\n')
    put(tmp_path, 'test_api.py', 'from api import expire\nvalue=expire()\ndef test_value(): assert value==1\n')
    report = analyze(build(tmp_path), ['symbol:api.py#expire'])
    assert paths(report['test_selection']['focused']) == {'test_api.py'}
    assert all('passed' not in row for row in report['test_selection']['focused'])


def test_literal_import_helper_reaches_the_test_that_calls_it(tmp_path):
    put(tmp_path, 'api.py', 'def expire(): return 1\n')
    put(tmp_path, 'test_api.py', 'import importlib\ndef runner(): return importlib.import_module("api")\n'
        'def test_api(): assert runner().expire()==1\n')
    report = analyze(build(tmp_path), ['api.py'])
    assert paths(report['test_selection']['focused']) == {'test_api.py'}
    assert any(e['kind']=='dynamic_import' for e in report['test_selection']['focused'][0]['explanation'])


def test_same_file_candidates_are_deduplicated_in_the_partition(tmp_path):
    sample(tmp_path)
    put(tmp_path, 'test_call.py', 'from api import expire\ndef test_one(): assert expire()==1\n'
        'def test_two(): assert expire()==1\n')
    selection = analyze(build(tmp_path), ['api.py'])['test_selection']
    assert len(selection['focused']) == len(paths(selection['focused']))
    assert not paths(selection['focused']) & paths(selection['fallback'])


def test_declared_and_observed_candidates_retain_their_provenance(tmp_path):
    sample(tmp_path)
    put(tmp_path, 'impactgraph.json', json.dumps({'schema':1,'nodes':[],'edges':[
        {'source':'file:test_import.py','target':'file:api.py','kind':'tests'}]}))
    report = analyze(build(tmp_path), ['api.py'])
    item = next(n for n in report['test_selection']['focused'] if n['path']=='test_import.py')
    assert item['category'] == 'declared'
    assert item['explanation'][0]['origin'] == 'declared'


def test_depth_and_result_caps_do_not_establish_safe_exclusion(tmp_path):
    sample(tmp_path)
    report = analyze(build(tmp_path), ['api.py'], max_results=1, max_depth=1)
    assert not report['coverage']['complete']
    assert report['test_selection']['safe_to_exclude_fallback'] is False
    assert paths(report['test_selection']['focused']) <= paths(report['tests'])


def test_markdown_explains_focused_fallback_and_support_without_hiding_them(tmp_path):
    sample(tmp_path)
    output = markdown(analyze(build(tmp_path), ['api.py']))
    assert 'Focused test candidates' in output
    assert 'Broader fallback candidates' in output
    assert 'test_call.py' in output and 'test_import.py' in output
    assert 'safe' in output.lower() and 'exclude' in output.lower()
