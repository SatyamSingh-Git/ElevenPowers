"""Declared contracts and unsigned observations never outrun their provenance."""
import json

import pytest

from core.impact import build


def put(root, path, value):
    file = root / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(value) if not isinstance(value, str) else value, encoding='utf-8')
    return file


def fixture(root):
    put(root, 'api.py', 'x=1\n')
    put(root, 'session.py', 'x=1\n')
    return {'schema': 1, 'nodes': [
        {'id': 'route:login', 'kind': 'route', 'label': 'POST /login', 'path': 'api.py'},
        {'id': 'database:sessions', 'kind': 'database', 'label': 'sessions'}],
        'edges': [{'source': 'route:login', 'target': 'file:session.py', 'kind': 'uses'},
                  {'source': 'file:session.py', 'target': 'database:sessions', 'kind': 'depends_on'}]}


def test_declared_contract_links_have_declared_provenance(tmp_path):
    put(tmp_path, 'impactgraph.json', fixture(tmp_path))
    graph = build(tmp_path)
    assert graph.nodes['route:login'].path == 'api.py'
    assert graph.nodes['database:sessions'].kind == 'database'
    assert len([e for e in graph.edges if e.origin == 'declared']) == 2
    assert all(e.path == 'impactgraph.json' for e in graph.edges)


@pytest.mark.parametrize('change', [
    lambda v: v.update(schema=2),
    lambda v: v['nodes'][0].update(path='../outside.py'),
    lambda v: v['nodes'][0].update(path='missing.py'),
    lambda v: v['nodes'].append(dict(v['nodes'][0])),
    lambda v: v['nodes'][0].update(id='file:api.py'),
    lambda v: v['edges'][0].update(target='route:missing'),
    lambda v: v['edges'][0].update(kind='execute'),
    lambda v: v.update(nodes='invalid'),
])
def test_invalid_declared_map_is_rejected_atomically(tmp_path, change):
    value = fixture(tmp_path)
    change(value)
    put(tmp_path, 'impactgraph.json', value)
    graph = build(tmp_path)
    assert not any(e.origin == 'declared' for e in graph.edges)
    assert 'route:login' not in graph.nodes
    assert 'declaration' in ' '.join(graph.issues)


def observation(root, fingerprint=None, complete=True):
    if fingerprint is None:
        fingerprint = build(root).fingerprint
    return {'schema': 1, 'producer': 'coverage-adapter 1', 'run': 'local-run-1',
            'complete': complete, 'source_fingerprint': fingerprint,
            'edges': [{'source': 'file:api.py', 'target': 'file:session.py',
                       'kind': 'observed_call'}]}


def test_complete_observation_bound_to_current_inputs(tmp_path):
    fixture(tmp_path)
    artifact = put(tmp_path, '.elevenpowers/impact-observations.json', observation(tmp_path))
    value = build(tmp_path, observations=artifact)
    edges = [e for e in value.edges if e.origin == 'observed']
    assert len(edges) == 1
    assert edges[0].identity == 'coverage-adapter 1/local-run-1'
    assert not value.quarantined


@pytest.mark.parametrize('change', [
    lambda v: v.update(source_fingerprint='0' * 64),
    lambda v: v.update(complete=False),
    lambda v: v.update(complete='true'),
    lambda v: v.update(producer=''),
    lambda v: v.update(schema=2),
    lambda v: v['edges'][0].update(target='file:missing.py'),
    lambda v: v['edges'][0].update(kind='calls'),
])
def test_unqualified_observation_never_enters_active_graph(tmp_path, change):
    fixture(tmp_path)
    value = observation(tmp_path)
    change(value)
    artifact = put(tmp_path, 'observations.json', value)
    graph = build(tmp_path, observations=artifact)
    assert not any(e.origin == 'observed' for e in graph.edges)
    assert graph.quarantined and graph.issues


def test_dirty_source_and_new_file_stale_observations(tmp_path):
    fixture(tmp_path)
    artifact = put(tmp_path, '.elevenpowers/observations.json', observation(tmp_path))
    put(tmp_path, 'session.py', 'x=2\n')
    assert build(tmp_path, observations=artifact).quarantined
    value = observation(tmp_path)
    artifact.write_text(json.dumps(value))
    put(tmp_path, 'added.py', 'x=1\n')
    assert build(tmp_path, observations=artifact).quarantined


def test_map_change_stales_observation(tmp_path):
    declaration = fixture(tmp_path)
    put(tmp_path, 'impactgraph.json', declaration)
    artifact = put(tmp_path, '.elevenpowers/observations.json', observation(tmp_path))
    declaration['nodes'][0]['label'] = 'renamed route'
    put(tmp_path, 'impactgraph.json', declaration)
    assert build(tmp_path, observations=artifact).quarantined


def test_row_limit_and_broken_json_are_explicit(tmp_path):
    declaration = fixture(tmp_path)
    declaration['edges'] *= 5001
    put(tmp_path, 'impactgraph.json', declaration)
    assert 'row limit' in ' '.join(build(tmp_path).issues)
    put(tmp_path, 'impactgraph.json', '{broken')
    assert 'declaration' in ' '.join(build(tmp_path).issues)


def test_observation_path_cannot_leave_project(tmp_path):
    with pytest.raises(ValueError):
        build(tmp_path, observations='../outside.json')
