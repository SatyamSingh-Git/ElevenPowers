"""Explained impact stays separate from test results and history associations."""
import json
import subprocess

import pytest

from core.impact import build


def put(root, path, text):
    file = root / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(text, encoding='utf-8')


def query(root, files, **kwargs):
    from core.impact import analyze
    return analyze(build(root), files, **kwargs)


def fixture(root):
    put(root, 'session.py', 'def expire(): return 1\n')
    put(root, 'api.py', 'from session import expire\ndef login(): return expire()\n')
    put(root, 'worker.py', 'from api import login\nlogin()\n')
    put(root, 'tests/test_worker.py', 'from worker import login\ndef test_worker(): assert login()\n')
    put(root, 'unrelated.py', 'def expire(): return 2\n')


def test_direct_transitive_and_relevant_tests_are_explained(tmp_path):
    fixture(tmp_path)
    result = query(tmp_path, ['session.py'])
    affected = {n['path']: n for n in result['affected']}
    assert {'api.py', 'worker.py'} <= affected.keys()
    assert 'unrelated.py' not in affected
    assert 'session.py' not in affected
    assert affected['api.py']['distance'] == 1
    assert affected['worker.py']['distance'] == 2
    assert affected['worker.py']['explanation'][0]['source'] == 'file:worker.py'
    assert 'tests/test_worker.py' in [n['path'] for n in result['tests']]
    assert 'passed' not in result['tests'][0]
    assert result['coverage']['complete']


def test_contract_node_and_multiple_file_seeds(tmp_path):
    fixture(tmp_path)
    put(tmp_path, 'impactgraph.json', json.dumps({'schema': 1, 'nodes': [
        {'id': 'database:sessions', 'kind': 'database', 'label': 'sessions'}], 'edges': [
        {'source': 'file:session.py', 'target': 'database:sessions', 'kind': 'depends_on'}]}))
    result = query(tmp_path, ['database:sessions'])
    assert 'session.py' in [n['path'] for n in result['affected']]
    result = query(tmp_path, ['session.py', 'worker.py'])
    assert 'worker.py' not in [n['path'] for n in result['affected']]
    assert result['tests']


def test_cycles_terminate_and_seed_is_not_its_own_impact(tmp_path):
    put(tmp_path, 'a.py', 'import b\n')
    put(tmp_path, 'b.py', 'import a\n')
    result = query(tmp_path, ['a.py'])
    assert [n['path'] for n in result['affected']] == ['b.py']


def test_missing_deleted_paths_and_query_caps_are_explicit(tmp_path):
    fixture(tmp_path)
    assert not query(tmp_path, ['deleted.py'])['coverage']['complete']
    assert not query(tmp_path, ['session.py'], max_depth=1)['coverage']['complete']
    assert not query(tmp_path, ['session.py'], max_results=1)['coverage']['complete']
    assert query(tmp_path, ['unrelated.py'], max_depth=1)['coverage']['complete']
    assert 'No current' in query(tmp_path, ['unrelated.py'])['summary']


@pytest.mark.parametrize('kwargs', [{'max_depth': 0}, {'max_depth': 21}, {'max_results': 1001}])
def test_invalid_query_limits_rejected(tmp_path, kwargs):
    fixture(tmp_path)
    with pytest.raises(ValueError):
        query(tmp_path, ['session.py'], **kwargs)


def test_test_declared_and_observed_path_provenance_retained(tmp_path):
    from core.impact import analyze
    put(tmp_path, 'session.py', 'x=1\n')
    put(tmp_path, 'tests/test_session.py', 'def test_session(): assert True\n')
    put(tmp_path, 'impactgraph.json', json.dumps({'schema': 1, 'nodes': [], 'edges': [
        {'source': 'file:tests/test_session.py', 'target': 'file:session.py', 'kind': 'tests'}]}))
    value = build(tmp_path)
    result = analyze(value, ['session.py'])
    assert result['tests'][0]['category'] == 'declared'
    assert result['tests'][0]['explanation'][0]['kind'] == 'tests'
    artifact = tmp_path / '.elevenpowers/observations.json'
    artifact.parent.mkdir()
    artifact.write_text(json.dumps({'schema': 1, 'producer': 'coverage', 'run': 'run-1',
        'complete': True, 'source_fingerprint': value.fingerprint, 'edges': [
        {'source': 'file:tests/test_session.py', 'target': 'file:session.py', 'kind': 'observed_test'}]}))
    # Remove declaration edge so the observed path is the only witness.
    put(tmp_path, 'impactgraph.json', '{"schema":1,"nodes":[],"edges":[]}')
    record = json.loads(artifact.read_text())
    record['source_fingerprint'] = build(tmp_path).fingerprint
    artifact.write_text(json.dumps(record))
    result = analyze(build(tmp_path, observations=artifact), ['session.py'])
    assert result['tests'][0]['category'] == 'observed'
    put(tmp_path, 'session.py', 'x=2\n')
    result = analyze(build(tmp_path, observations=artifact), ['session.py'])
    assert not result['tests'] and result['quarantined']


def test_git_co_change_is_separate_from_causal_paths(tmp_path):
    from core.impact import analyze
    def git(*args):
        return subprocess.run(['git', '-c', f'safe.directory={tmp_path.as_posix()}',
            '-c', 'user.name=fixture', '-c', 'user.email=fixture@example.invalid', *args],
            cwd=tmp_path, check=True, capture_output=True)
    git('init', '-q')
    put(tmp_path, 'session.py', 'x=1\n')
    put(tmp_path, 'unrelated.py', 'x=1\n')
    git('add', '.')
    git('commit', '-qm', 'fixture')
    value = build(tmp_path, history=1)
    result = analyze(value, ['session.py'])
    assert not result['affected']
    assert result['associations'][0]['path'] == 'unrelated.py'
    assert result['associations'][0]['origin'] == 'historical'


def test_non_git_requested_history_is_incomplete(tmp_path):
    put(tmp_path, 'app.py', 'x=1\n')
    assert 'history' in ' '.join(build(tmp_path, history=1).issues)
