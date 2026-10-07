import json

import pytest


def test_frozen_labels_grade_misses_negatives_and_fallback_separately():
    from eval.milestone_rechecks import grade
    case = {'required': ['consumer'], 'negative': ['other']}
    report = {'coverage': {'complete': True}, 'rechecks': {'state': 'available', 'commands': [
        {'priority': 'fallback', 'milestones': [{'id': 'consumer', 'state': 'STALE'}]},
        {'priority': 'direct', 'milestones': [{'id': 'other', 'state': 'STALE'}]}]}}
    value = grade(case, report)
    assert value['hits'] == [] and value['misses'] == ['consumer']
    assert value['false_leads'] == ['other'] and value['fallback_retained'] == ['consumer']
    assert value['known_required'] == 1 and value['known_negatives'] == 1


def test_controller_keeps_every_attempt_and_detects_fault_and_equivalence(tmp_path):
    from eval.milestone_rechecks import exercise
    destination = tmp_path / 'new'
    value = exercise(destination, case_ids=['python-chain', 'configuration', 'subprocess-worker', 'unrelated-edit'], repeats=1)
    assert value['qualified']
    assert len(value['cases']) == 4
    for case in value['cases']:
        assert case['frozen_checks_unchanged']
        assert case['baseline']['qualified'] and case['equivalent']['qualified']
        assert len(case['reads']) == 3
        assert all(sample['plain_ms'] >= 0 and sample['advised_ms'] >= 0 for sample in case['reads'])
        assert all(sample['ledger_unchanged'] for sample in case['reads'])
    worker = next(c for c in value['cases'] if c['id'] == 'subprocess-worker')
    assert worker['fault']['qualified'] and worker['grade']['misses'] == ['worker']
    assert worker['grade']['fallback_retained'] == ['worker']
    unrelated = next(c for c in value['cases'] if c['id'] == 'unrelated-edit')
    assert not unrelated['grade']['false_leads']
    assert unrelated['fault']['before_states'] == {'feature': 'STALE'}
    assert json.loads((destination / 'observations.json').read_text())['corpus_sha256'] == value['corpus_sha256']
    with pytest.raises(FileExistsError):
        exercise(destination, case_ids=['python-chain'])


def test_invalid_case_and_repeat_budget_rejected_before_creating_output(tmp_path):
    from eval.milestone_rechecks import exercise
    for kwargs in ({'case_ids': ['unknown']}, {'repeats': 0}, {'repeats': True}, {'repeats': 6}):
        with pytest.raises(ValueError):
            exercise(tmp_path / 'absent', **kwargs)
        assert not (tmp_path / 'absent').exists()
