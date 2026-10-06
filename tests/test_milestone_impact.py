import json
import time

import pytest

from core.ledger import Ledger
from core.milestones import build
from test_milestone_history import project, receipt


def consumer_project(root):
    project(root)
    (root / 'consumer.py').write_text('from provider import value\n\ndef accept():\n    return value\n')
    value = json.loads((root / 'elevenpowers.milestones.json').read_text())
    value['milestones'][0]['inputs'] = ['consumer.py', 'tests/test_login.py']
    (root / 'elevenpowers.milestones.json').write_text(json.dumps(value))
    ledger = Ledger(root=root, task='first', touched=['provider.py'])
    ledger.add([receipt(root)]); ledger.save()
    return root


def test_graph_explains_earlier_behavior_consumer_without_certifying_a_break(tmp_path):
    root = consumer_project(tmp_path)
    value = build(root, impact=True, changed=['provider.py'])
    leads = value['impact']['leads']
    assert any(l['milestone'] == 'login' and l['input'] == 'consumer.py' and l['explanation'] for l in leads)
    assert value['milestones'][0]['state'] == 'CURRENT'
    assert value['impact']['safe_to_exclude'] is False


def test_current_task_touched_paths_are_default_change_observations(tmp_path):
    value = build(consumer_project(tmp_path), impact=True)
    assert value['impact']['requested'] == ['provider.py']
    assert value['impact']['leads']


def test_no_path_does_not_prove_that_a_behavior_is_unaffected(tmp_path):
    root = consumer_project(tmp_path)
    (root / 'unrelated.py').write_text('unrelated = 1\n')
    value = build(root, impact=True, changed=['unrelated.py'])
    assert not value['impact']['leads']
    assert value['impact']['safe_to_exclude'] is False
    assert any('unaffected' in line for line in value['impact']['limits'])


def test_missing_change_observations_and_unsafe_paths_are_explicit(tmp_path):
    project(tmp_path)
    value = build(tmp_path, impact=True)
    assert value['state'] == 'INCOMPLETE' and value['impact']['issues']
    with pytest.raises(ValueError):
        build(tmp_path, impact=True, changed=['../escape.py'])


def test_direct_impact_leads_are_bounded_even_without_graph_candidates(tmp_path, monkeypatch):
    import core.milestones.impact as bridge
    paths = [f'file{i}.py' for i in range(128)]
    rows = [{'id': f'stage{i}', 'inputs': paths} for i in range(4)]
    monkeypatch.setattr(bridge, 'graph_build', lambda *args, **kwargs: {})
    monkeypatch.setattr(bridge, 'analyze', lambda *args: {
        'source_fingerprint': '', 'coverage': {'issues': []}, 'affected': [], 'tests': []})
    value = bridge.advise(tmp_path, rows, paths, deadline=time.monotonic() + 10)
    assert len(value['leads']) <= 256
    assert value['state'] == 'incomplete' and value['issues']


def test_changed_paths_need_impact_even_without_project_declarations(tmp_path):
    with pytest.raises(ValueError, match='changed paths require'):
        build(tmp_path, changed=['provider.py'])
