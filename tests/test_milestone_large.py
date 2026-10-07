import hashlib
import json

import pytest


def test_sealed_snapshot_rejects_changed_and_unfrozen_inputs(tmp_path):
    from eval.milestone_large import inspect
    (tmp_path / 'source.py').write_text('value = 1\n')
    seal = {'source.py': hashlib.sha256((tmp_path / 'source.py').read_bytes()).hexdigest()}
    assert inspect(tmp_path, seal)['complete']
    (tmp_path / 'source.py').write_text('value = 2\n')
    assert not inspect(tmp_path, seal)['complete']
    (tmp_path / 'new.py').write_text('unfrozen = True\n')
    assert any('unfrozen' in i for i in inspect(tmp_path, seal)['issues'])


def test_larger_evaluation_declines_unsealed_project_before_reporting(tmp_path):
    from eval.milestone_large import evaluate
    corpus = {'schema': 1, 'projects': [{'id': 'project', 'files': {'absent.py': '0' * 64}}],
              'cases': [{'id': 'case', 'project': 'project', 'query': 'absent.py',
                         'required': ['behavior'], 'negative': []}]}
    result = evaluate(corpus, {'project': str(tmp_path)}, repeats=1)
    assert result['state'] == 'incomplete' and result['projects'][0]['seal']['issues']
    assert not result['cases']


def test_evaluation_preserves_unknown_leads_and_cost_samples(tmp_path):
    from eval.milestone_large import evaluate
    from test_milestone_entrypoints import process_project
    process_project(tmp_path)
    files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in tmp_path.iterdir()}
    corpus = {'schema': 1, 'projects': [{'id': 'project', 'files': files}],
              'cases': [{'id': 'case', 'project': 'project', 'query': 'other.py',
                         'required': [], 'negative': ['cli']}]}
    result = evaluate(corpus, {'project': str(tmp_path)}, repeats=1)
    assert result['cases'][0]['grade']['unlabelled_leads'] == ['other']
    assert len(result['cases'][0]['samples']) == 1
    assert result['cases'][0]['samples'][0]['advised_ms'] >= 0
    assert not (tmp_path / '.elevenpowers').exists()
    with pytest.raises(ValueError):
        evaluate(corpus, {'project': str(tmp_path)}, repeats=True)
