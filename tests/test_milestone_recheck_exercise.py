import json

import pytest


def test_frozen_labels_grade_misses_negatives_and_fallback_separately():
    from eval.milestone_rechecks import grade
    case = {'required': ['consumer'], 'negative': ['other']}
    report = {'coverage': {'complete': True}, 'rechecks': {'state': 'available', 'commands': [
        {'priority': 'fallback', 'milestones': [{'id': 'consumer', 'state': 'STALE'}], 'reasons': []},
        {'priority': 'direct', 'milestones': [{'id': 'other', 'state': 'STALE'}],
         'reasons': [{'milestone': 'other'}]}]}}
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


def test_shared_command_does_not_invent_a_relationship_for_other_milestones():
    from core.milestones.rechecks import plan
    from eval.milestone_rechecks import grade
    from test_milestone_rechecks import advice, lead, row
    report = {'coverage': {'complete': True}, 'rechecks': plan(
        [row('witnessed', 'STALE'), row('missing', 'STALE'), row('unrelated', 'STALE')],
        advice([lead('witnessed')]), complete=True)}
    result = grade({'required': ['witnessed', 'missing'], 'negative': ['unrelated']}, report)
    assert result['hits'] == ['witnessed'] and result['misses'] == ['missing']
    assert result['fallback_retained'] == ['missing'] and not result['false_leads']


def test_interruption_keeps_finished_attempts_and_pending_source_identity(tmp_path, monkeypatch):
    import eval.milestone_rechecks as controller
    original = controller.Producer.execute
    calls = 0
    def interrupted(self, *args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError('controlled interruption after one real attempt')
        return original(self, *args, **kwargs)
    monkeypatch.setattr(controller.Producer, 'execute', interrupted)
    destination = tmp_path / 'new'
    value = controller.exercise(destination, case_ids=['python-chain'], repeats=1)
    assert not value['qualified']
    saved = json.loads((destination / 'observations.json').read_text())
    case = saved['cases'][0]
    assert case['state'] == 'incomplete' and case['issues']
    assert len(case['runs']) == 1 and case['runs'][0]['phase'] == 'baseline'
    assert case['runs'][0]['source_fingerprint'] and case['reads']
    assert case['pending_attempt']['milestone'] == 'delivery'
    assert case['pending_attempt']['source_fingerprint']


def test_corrected_grader_preserves_all_original_published_grades():
    from pathlib import Path
    from eval.milestone_rechecks import CORPUS, grade
    corpus = {c['id']: c for c in json.loads(CORPUS.read_text())['cases']}
    original = json.loads((Path(__file__).parents[1] / 'results/milestone-rechecks/observations.v1.json').read_text())
    for case in original['cases']:
        report = {'coverage': {'complete': case['grade']['coverage_complete']}, 'rechecks': case['recommendations']}
        assert grade(corpus[case['id']], report) == case['grade']
