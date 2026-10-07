import json
import time

from core.milestones import build, markdown
from test_milestone_impact import consumer_project


def row(name, state, command='python -m pytest', kind='test_suite'):
    return {'id': name, 'checks': [{'kind': kind, 'command': command, 'state': state,
                                   'issues': [], 'qualifications': ['declared inputs only']}]}


def advice(leads=(), issues=()):
    return {'state': 'incomplete' if issues else 'available', 'leads': list(leads),
            'issues': list(issues), 'safe_to_exclude': False}


def lead(name, category='direct change observation', path='src/value.py'):
    return {'milestone': name, 'input': path, 'category': category, 'explanation': []}


def test_shared_exact_command_keeps_every_milestone_state_and_fallback():
    from core.milestones.rechecks import plan
    value = plan([row('first', 'CURRENT'), row('second', 'STALE'),
                  row('other', 'ABSENT', 'python -m pytest tests/other.py')],
                 advice([lead('first')]), complete=True)
    assert len(value['commands']) == 2
    shared = value['commands'][0]
    assert shared['priority'] == 'direct' and shared['needs_refresh']
    assert shared['milestones'] == [{'id': 'first', 'state': 'CURRENT'},
                                    {'id': 'second', 'state': 'STALE'}]
    assert shared['qualifications'] == ['declared inputs only']
    assert value['commands'][1]['priority'] == 'fallback'
    assert value['safe_to_exclude'] is False


def test_ranking_is_separate_from_freshness_and_does_not_invent_commands():
    from core.milestones.rechecks import plan
    rows = [row('current', 'CURRENT', 'check current'), row('dependent', 'FAILED', 'check dep'),
            row('unknown', 'STALE', 'check unknown'), row('same-spelling', 'ABSENT', 'check dep', 'build')]
    value = plan(rows, advice([lead('current'), lead('dependent', 'transitive')]), complete=True)
    assert [c['command'] for c in value['commands']] == ['check dep', 'check dep', 'check unknown', 'check current']
    assert len(value['commands']) == 4  # kind is part of exact identity
    assert value['commands'][-1]['needs_refresh'] is False
    assert value['commands'][0]['priority'] == 'dependency'
    assert all(c['origin'] == 'project declaration' for c in value['commands'])


def test_incomplete_advice_keeps_all_fallbacks_and_cannot_certify_exclusion():
    from core.milestones.rechecks import plan
    value = plan([row('first', 'CURRENT'), row('second', 'CURRENT', 'other')],
                 advice(issues=['graph deadline']), complete=False)
    assert value['state'] == 'incomplete'
    assert len(value['commands']) == 2
    assert all(c['priority'] == 'fallback' and not c['needs_refresh'] for c in value['commands'])
    assert value['issues'] and not value['safe_to_exclude']


def test_reason_budget_preserves_rows_and_reports_omissions():
    from core.milestones.rechecks import plan
    value = plan([row('first', 'STALE')], advice([lead('first', path=f'{i}.py') for i in range(20)]), complete=True)
    assert len(value['commands'][0]['reasons']) == 16
    assert value['commands'][0]['omitted_reasons'] == 4
    assert value['state'] == 'incomplete' and value['issues']


def test_existing_report_adds_exact_recheck_explanations_without_mutation(tmp_path):
    root = consumer_project(tmp_path)
    before = {p: p.read_bytes() for p in root.rglob('*') if p.is_file()}
    value = build(root, impact=True, changed=['provider.py'])
    checks = value['rechecks']['commands']
    assert len(checks) == 1 and checks[0]['priority'] == 'dependency'
    assert checks[0]['command'] == 'python -m pytest tests/test_login.py'
    assert checks[0]['needs_refresh'] is False
    assert checks[0]['reasons'][0]['explanation']
    assert 'Recommended recheck order' in markdown(value)
    assert 'dependency' in markdown(value)
    assert value['timings']['impact_ms'] >= 0
    assert value['impact']['timings']['graph_ms'] >= 0
    assert value['rechecks']['state'] == 'available'
    assert value['state'] == 'CURRENT'
    assert before == {p: p.read_bytes() for p in root.rglob('*') if p.is_file()}
    assert build(root)['rechecks']['state'] == 'not_requested'


def test_direct_match_survives_no_time_for_graph(tmp_path):
    from core.milestones.impact import advise
    value = advise(tmp_path, [{'id': 'first', 'inputs': ['settings.json']}],
                   ['settings.json'], deadline=time.monotonic() - 1)
    assert value['leads'] == [lead('first', path='settings.json')]
    assert value['state'] == 'incomplete' and value['issues']


def test_observation_storage_is_bounded_and_omissions_visible(tmp_path, monkeypatch):
    import core.milestones.impact as bridge
    monkeypatch.setattr(bridge, 'graph_build', lambda *a, **kw: {})
    monkeypatch.setattr(bridge, 'analyze', lambda *a, **kw: {
        'source_fingerprint': 'x', 'coverage': {'issues': []}, 'affected': [], 'tests': []})
    value = bridge.advise(tmp_path, [], [f'{i}.py' for i in range(257)], deadline=time.monotonic() + 10)
    assert len(value['requested']) == 256 and value['omitted_observations'] == 1
    assert value['state'] == 'incomplete'


def test_graph_snapshot_movement_marks_advice_incomplete_without_changing_check_state(tmp_path, monkeypatch):
    import core.milestones.impact as bridge
    original = bridge.advise
    def moved(*args, **kwargs):
        value = original(*args, **kwargs)
        value['evidence_source_fingerprint'] = 'different'
        return value
    monkeypatch.setattr(bridge, 'advise', moved)
    value = build(consumer_project(tmp_path), impact=True, changed=['provider.py'])
    assert value['state'] == 'INCOMPLETE'
    assert value['milestones'][0]['state'] == 'CURRENT'
    assert value['rechecks']['state'] == 'incomplete'
    assert any('source snapshot' in i for i in value['coverage']['issues'])


def test_explanation_omissions_cannot_pass_the_requested_report_gate(tmp_path, monkeypatch):
    import core.milestones.rechecks as recommendations
    original = recommendations.plan
    def truncated(*args, **kwargs):
        value = original(*args, **kwargs)
        value.update(state='incomplete', issues=['command explanation limit 16 reached'])
        return value
    monkeypatch.setattr(recommendations, 'plan', truncated)
    value = build(consumer_project(tmp_path), impact=True, changed=['provider.py'])
    assert value['state'] == 'INCOMPLETE' and not value['coverage']['complete']
    assert value['milestones'][0]['state'] == 'CURRENT'
