"""The acted-on experiment's harness: certification, grading, workspace. No model.

Design: docs/superpowers/specs/2026-11-04-rule-groups-acted-on-design.md
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYROLL = ROOT / 'eval' / 'multistage_v3' / 'payroll_lite'


def _case():
    from eval.multistage_cases import load
    return load(PAYROLL)


def test_certification_accepts_only_pairs_that_a_stage_breaks(tmp_path):
    from eval.rule_groups_run import breaking_pairs, certify
    case = _case()
    entries = certify(case, tmp_path)
    pairs = {frozenset(e['inputs']) for e in entries}
    assert frozenset({'src/payroll/rules/overtime.py', 'src/payroll/reports/hours.py'}) in pairs
    assert pairs <= breaking_pairs(case, tmp_path / 'again')


def test_a_certified_description_borrows_no_word_from_any_request(tmp_path):
    from eval.rule_groups_run import certify
    case = _case()
    for entry in certify(case, tmp_path):
        assert entry['description'].startswith('These files keep the same rule (they share ')
        assert entry['checks'] == [{'kind': 'test_suite', 'command': f"python -m pytest {case['test_dir']} -q"}]


def test_a_stage_is_graded_lost_only_when_its_dependent_is_left_behind(tmp_path):
    from eval.multistage_cases import tree
    from eval.rule_groups_run import outcome
    case = _case()
    before = tree(case, 1, tmp_path / 'before')
    assert outcome(case, 2, before, tree(case, 2, tmp_path / 'reference'))['dependent_lost'] is False
    assert outcome(case, 2, before, tree(case, 2, tmp_path / 'quiet', 'quiet'))['dependent_lost'] is True


def test_another_group_lost_is_not_the_dependent_left_behind(monkeypatch):
    # The mapping from lost groups to the stage's dependent, with the oracles' answers given.
    from eval import rule_groups_run
    case = _case()
    other = next(g['id'] for g in case['groups'] if g['since'] == 0 and g['id'] != 'base_consistency' and g['until'] >= 2)
    answers = iter([{other: 'passed', 'base_consistency': 'passed'}, {other: 'failed', 'base_consistency': 'passed'}])
    monkeypatch.setattr(rule_groups_run.oracles, 'groups', lambda *args, **kw: next(answers))
    graded = rule_groups_run.outcome(case, 2, 'before', 'after')
    assert graded['lost'] == [other] and graded['dependent_lost'] is False


def test_only_the_rules_arm_carries_the_declarations(tmp_path):
    from eval.rule_groups_run import certify, workspace
    case = _case()
    entries = certify(case, tmp_path / 'certify')
    control = workspace(case, 2, 'control', tmp_path / 'control', entries)
    rules = workspace(case, 2, 'rules', tmp_path / 'rules', entries)
    assert not (control / 'elevenpowers.milestones.json').exists()
    declared = json.loads((rules / 'elevenpowers.milestones.json').read_text(encoding='utf-8'))
    assert declared == {'schema': 1, 'milestones': entries}
    for work in (control, rules):
        assert (work / '.claude' / 'settings.local.json').exists()
        assert (work / 'src/payroll/rules/overtime.py').read_bytes() == (rules / 'src/payroll/rules/overtime.py').read_bytes()



# --- the sealed one-stage runner, with only the external model process substituted ---

def _fake(plan, *, model='claude-sonnet-5-5', loaded=True, briefed=()):
    """The fake host plays the agent: 'reference' applies the stage's change, 'quiet' leaves the dependent behind.
    `briefed` stands in for the files the real hook would have briefed."""
    from types import SimpleNamespace
    from eval import rule_groups_run as m
    from eval.bundle import apply_patch
    actual, calls = m.run, []

    def external(command, **kwargs):
        if not (isinstance(command, list) and command[0] == 'fake-host'):
            return actual(command, **kwargs)
        if command[-1] == '--version':
            return SimpleNamespace(returncode=0, stdout='fake test host', stderr='')
        root = Path(kwargs['cwd'])
        case = json.loads((PAYROLL / 'case.json').read_text(encoding='utf-8'))
        stage = next(n for n, s in enumerate(case['stages'], 1) if s['request'] in command[2])
        session = command[command.index('--session-id') + 1]
        declarations = root / 'elevenpowers.milestones.json'
        calls.append({'stage': stage, 'root': root, 'declared': declarations.exists(),
                      'declarations': json.loads(declarations.read_text(encoding='utf-8')) if declarations.exists() else None})
        diffs = ['reference.diff'] + (['quiet-0.diff'] if plan == 'quiet' else [])
        for name in diffs:
            assert not apply_patch(root, (PAYROLL / 'stages' / str(stage) / name).read_text(encoding='utf-8'))
        if briefed:
            ledger = root / '.elevenpowers' / 'ledger.json'
            state = json.loads(ledger.read_text(encoding='utf-8')) if ledger.exists() else {}
            ledger.parent.mkdir(exist_ok=True)
            ledger.write_text(json.dumps({**state, 'briefed': list(briefed)}), encoding='utf-8')
        events = [{'type': 'system', 'subtype': 'hook_response', 'hook_name': 'SessionStart:startup',
                   'output': json.dumps({'hookSpecificOutput': {'additionalContext': 'ElevenPowers active (profile: guide).'}})}
                  if loaded else {'type': 'system', 'subtype': 'hook_started'},
                  {'type': 'system', 'subtype': 'init', 'session_id': session,
                   'plugins': [{'source': 'superpowers@claude-plugins-official'}]},
                  {'type': 'result', 'is_error': False, 'session_id': session, 'result': 'done',
                   'total_cost_usd': 0.15, 'modelUsage': {model: {}}}]
        return SimpleNamespace(returncode=0, stdout='\n'.join(json.dumps(e) for e in events), stderr='')
    external.calls = calls
    return external


def _prepared(tmp_path, monkeypatch):
    from eval import rule_groups_run as m
    monkeypatch.setattr(m.subscription, 'auth', lambda *a: True)
    return m.prepare(tmp_path / 'batch', [('payroll_lite', 2)], replicates=1, seconds=60)


def test_slots_pair_the_arms_on_each_stage_and_freeze_the_certified_rules(tmp_path, monkeypatch):
    protocol = _prepared(tmp_path, monkeypatch)
    assert sorted(protocol['slots']) == ['payroll_lite--2--control--0', 'payroll_lite--2--rules--0']
    assert any('src/payroll/reports/hours.py' in e['inputs'] for e in protocol['rules']['payroll_lite'])


def test_a_stage_left_behind_is_graded_lost_and_a_completed_one_kept(tmp_path, monkeypatch):
    from eval import rule_groups_run as m
    _prepared(tmp_path, monkeypatch)
    monkeypatch.setattr(m, 'run', _fake('quiet'))
    lost = m.execute(tmp_path / 'batch', 'payroll_lite--2--control--0', 'fake-host')
    monkeypatch.setattr(m, 'run', _fake('reference'))
    kept = m.execute(tmp_path / 'batch', 'payroll_lite--2--rules--0', 'fake-host')
    assert (lost['state'], lost['outcome']['dependent_lost']) == ('completed', True)
    assert (kept['state'], kept['outcome']['dependent_lost']) == ('completed', False)


def test_only_the_rules_arm_runs_with_the_declarations(tmp_path, monkeypatch):
    from eval import rule_groups_run as m
    _prepared(tmp_path, monkeypatch)
    host = _fake('reference')
    monkeypatch.setattr(m, 'run', host)
    for slot in ('payroll_lite--2--control--0', 'payroll_lite--2--rules--0'):
        m.execute(tmp_path / 'batch', slot, 'fake-host')
    assert sorted(c['declared'] for c in host.calls) == [False, True]


def test_a_run_where_elevenpowers_did_not_load_is_not_comparable(tmp_path, monkeypatch):
    from eval import rule_groups_run as m
    _prepared(tmp_path, monkeypatch)
    monkeypatch.setattr(m, 'run', _fake('reference', loaded=False))
    assert m.execute(tmp_path / 'batch', 'payroll_lite--2--rules--0', 'fake-host')['state'] == 'plugins_unqualified'


def test_a_launched_slot_is_never_relaunched(tmp_path, monkeypatch):
    import pytest
    from eval import rule_groups_run as m
    _prepared(tmp_path, monkeypatch)
    monkeypatch.setattr(m, 'run', _fake('reference'))
    m.execute(tmp_path / 'batch', 'payroll_lite--2--rules--0', 'fake-host')
    with pytest.raises(ValueError, match='never retry'):
        m.execute(tmp_path / 'batch', 'payroll_lite--2--rules--0', 'fake-host')


def test_a_changed_protocol_is_refused(tmp_path, monkeypatch):
    import pytest
    from eval import rule_groups_run as m
    _prepared(tmp_path, monkeypatch)
    path = tmp_path / 'batch' / 'protocol.json'
    path.write_text(path.read_text(encoding='utf-8').replace('"replicates": 1', '"replicates": 2'), encoding='utf-8')
    with pytest.raises(ValueError, match='sealed protocol changed'):
        m.execute(tmp_path / 'batch', 'payroll_lite--2--rules--0', 'fake-host')


def _described(tmp_path, monkeypatch, descriptions=None, arms=('rules', 'described')):
    from eval import rule_groups_run as m
    monkeypatch.setattr(m.subscription, 'auth', lambda *a: True)
    if descriptions is None:
        ids = [e['id'] for e in m.certify(_case(), tmp_path / 'ids')]
        descriptions = {'payroll_lite': {i: f'Reviewer sentence for {i}.' for i in ids}}
    return m.prepare(tmp_path / 'batch', [('payroll_lite', 2)], replicates=1, seconds=60,
                     arms=arms, descriptions=descriptions)


def test_the_described_arm_keeps_the_certified_rules_in_a_reviewer_s_words(tmp_path, monkeypatch):
    protocol = _described(tmp_path, monkeypatch)
    assert sorted(protocol['slots']) == ['payroll_lite--2--described--0', 'payroll_lite--2--rules--0']
    rules, described = protocol['rules']['payroll_lite'], protocol['described']['payroll_lite']
    assert [{**e, 'description': ''} for e in described] == [{**e, 'description': ''} for e in rules]
    assert [e['description'] for e in described] == [f"Reviewer sentence for {e['id']}." for e in rules]


def test_descriptions_must_name_exactly_the_certified_rules(tmp_path, monkeypatch):
    import pytest
    from eval import rule_groups_run as m
    ids = [e['id'] for e in m.certify(_case(), tmp_path / 'ids')]
    for n, given in enumerate(({i: 'x' for i in ids[1:]}, {**{i: 'x' for i in ids}, 'rule-made-up': 'x'})):
        with pytest.raises(ValueError, match='exactly its certified rules'):
            _described(tmp_path / str(n), monkeypatch, {'payroll_lite': given})
    with pytest.raises(ValueError, match='described arm'):
        m.prepare(tmp_path / 'none' / 'batch', [('payroll_lite', 2)], replicates=1, arms=('rules', 'described'))


def test_the_described_arm_runs_with_the_described_declarations(tmp_path, monkeypatch):
    from eval import rule_groups_run as m
    protocol = _described(tmp_path, monkeypatch)
    host = _fake('reference', briefed=['src/payroll/rules/overtime.py'])
    monkeypatch.setattr(m, 'run', host)
    for slot in protocol['slots']:
        record = m.execute(tmp_path / 'batch', slot, 'fake-host')
        assert (record['state'], record['declared_files_briefed']) == ('completed', ['src/payroll/rules/overtime.py'])
    seen = {c['declarations']['milestones'][0]['description'] for c in host.calls}
    assert seen == {protocol['rules']['payroll_lite'][0]['description'],
                    protocol['described']['payroll_lite'][0]['description']}


def test_the_stratified_test_is_exact_and_one_sided():
    from eval.rule_groups_run import stratified_p
    # One stratum, 0 of 3 lost with rules against 3 of 3 without: the hypergeometric tail is 1 in 20.
    assert abs(stratified_p([(0, 3, 3, 3)]) - 0.05) < 1e-12
    assert stratified_p([(3, 3, 0, 3)]) == 1.0
