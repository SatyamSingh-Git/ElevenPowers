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
