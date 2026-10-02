"""Free audit repairs grader blind spots without rewriting frozen run scores."""
import importlib.util


def test_hard_supplemental_audit_exists():
    assert importlib.util.find_spec('eval.hard_audit') is not None, 'supplemental audit is missing'


def test_visible_regression_failure_qualifies_even_a_perfect_hidden_grade(tmp_path):
    from eval import hard_cases as cases, hard_audit, proposals
    root=tmp_path/'candidate';cases.prepare('build-planner',root)
    for name,source in cases.gold('build-planner').items():(root/name).write_bytes(source.encode())
    (root/'tests/test_regression.py').write_text('import unittest\nclass Regression(unittest.TestCase):\n    def test_failed(self):self.fail("ordinary regression")\n')
    assert cases.grade('build-planner',root)['passed']==24
    value=hard_audit.audit_snapshot('build-planner',proposals.snapshot(root,cases.names('build-planner')))
    assert not value['qualified'] and value['visible']['exit_code']==1


def test_close_after_invalidation_observes_detached_fetch(tmp_path):
    from eval import hard_cases as cases, hard_audit, proposals
    root=tmp_path/'candidate';cases.prepare('async-cache',root)
    for name,source in cases.gold('async-cache').items():(root/name).write_bytes(source.encode())
    good=hard_audit.audit_snapshot('async-cache',proposals.snapshot(root,cases.names('async-cache')))
    assert good['qualified'] and good['additional']['close_detached_fetch']
    source=cases.gold('async-cache')['app/service.py'].replace('tasks=list(self.tasks)','tasks=[v[1] for v in self.flights.values()]')
    # Reproduce an ordinary close implementation that cancels only current flights.
    source=source.replace('self.values.clear();self.flights.clear()','self.values.clear()')
    (root/'app/service.py').write_bytes(source.encode())
    assert cases.grade('async-cache',root)['passed']==22
    bad=hard_audit.audit_snapshot('async-cache',proposals.snapshot(root,cases.names('async-cache')))
    assert not bad['qualified'] and not bad['additional']['close_detached_fetch']
