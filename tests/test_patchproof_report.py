import json
import time

import pytest

from core.evidence import Evidence, Kind, Result, source_snapshot, tree_hash
from core.ledger import Ledger
from tests.test_patchproof_identity import git, commit


@pytest.fixture
def project(tmp_path):
    git(tmp_path, 'init', '-q')
    git(tmp_path, 'config', 'core.autocrlf', 'false')
    (tmp_path / 'service.py').write_bytes(b'value=1\n')
    (tmp_path / 'unrelated.py').write_bytes(b'value=0\n')
    base = commit(tmp_path, 'base')
    (tmp_path / 'service.py').write_bytes(b'value=2\n')
    head = commit(tmp_path, 'patch')
    return tmp_path, base, head


def seed(root, *, result=Result.PASS, execution='complete', observed=None,
         declaration='', command='python -m pytest', counted=False, passed=0):
    scan, tree = source_snapshot(root, fresh=True)
    if observed is not None:
        tree = tree_hash(root, observed, fresh=True)
    record = Evidence(Kind.SUITE, 'suite', result,
                      scan.files if observed is None else observed, tree,
                      scope='source' if observed is None else '',
                      command=command, execution=execution, declaration=declaration,
                      declared_command=command if declaration else '', at=time.time(),
                      counted=counted, passed=passed, detail='private receipt detail')
    ledger = Ledger(root=root, task='task', request='private prompt', evidence=[record])
    ledger.save()
    return ledger


def test_current_input_association_does_not_invent_task_completion(project):
    from core.patchproof.report import build
    root, base, head = project
    seed(root)
    value = build(root, base, head)
    assert value['binding']['state'] == 'bound'
    assert value['receipts'][0]['association'] == 'bound'
    assert value['receipts'][0]['patch_paths'] == ['service.py']
    assert value['verification']['schema_version'] == 1
    assert value['verification']['state'] == 'UNVERIFIED'
    assert value['receipts'][0]['executed_at_patch_head'] == 'unknown'
    assert value['receipts'][0]['environment'] == 'unknown'


@pytest.mark.parametrize(('result', 'execution', 'state'), [
    (Result.PASS, 'complete', 'current'), (Result.FAIL, 'complete', 'failed'),
    (Result.PASS, 'incomplete', 'incomplete')])
def test_declared_results_execution_and_association_remain_separate(project, result, execution, state):
    from core.patchproof.report import build
    root, base, head = project
    (root / '.elevenpowers').mkdir(exist_ok=True)
    (root / '.elevenpowers/config.json').write_text(json.dumps({'auto_detect': False,
        'commands': {'suite_green': 'python -m pytest', 'build': 'python build.py'}}))
    seed(root, result=result, execution=execution, declaration='suite_green')
    value = build(root, base, head)
    assert value['checks'][0]['state'] == state
    assert value['checks'][1]['state'] == 'absent'
    assert value['receipts'][0]['result'] == result.value
    assert value['receipts'][0]['execution'] == execution
    assert value['receipts'][0]['association'] == 'bound'


@pytest.mark.parametrize('observed', [[], ['unrelated.py']])
def test_zero_or_unrelated_observations_cannot_bind_to_changed_paths(project, observed):
    from core.patchproof.report import build
    root, base, head = project
    seed(root, observed=observed)
    value = build(root, base, head)
    assert value['receipts'][0]['association'] == 'unavailable'
    assert value['coverage']['unobserved_patch_paths'] == ['service.py']


def test_stale_receipt_and_dirty_patch_never_bind(project):
    from core.patchproof.report import build
    root, base, head = project
    seed(root)
    (root / 'service.py').write_bytes(b'value=999\n')
    value = build(root, base, head)
    assert value['binding']['state'] == 'unavailable'
    assert value['receipts'][0]['freshness'] == 'stale'
    assert value['receipts'][0]['association'] == 'unavailable'


def test_receipts_before_commit_can_bind_to_unchanged_observed_bytes(project):
    from core.patchproof.report import build
    root, base, head = project
    (root / 'service.py').write_bytes(b'value=3\n')
    seed(root)
    new_head = commit(root, 'after recording')
    value = build(root, head, new_head)
    assert value['binding']['state'] == 'bound'
    assert value['receipts'][0]['association'] == 'bound'
    assert value['receipts'][0]['executed_at_patch_head'] == 'unknown'


def test_changed_command_declaration_expires_receipt(project):
    from core.patchproof.report import build
    root, base, head = project
    state = root / '.elevenpowers'
    state.mkdir()
    config = state / 'config.json'
    config.write_text(json.dumps({'commands': {'suite_green': 'old-check'}}))
    seed(root, declaration='suite_green', command='old-check')
    config.write_text(json.dumps({'commands': {'suite_green': 'new-check'}}))
    value = build(root, base, head)
    assert value['receipts'][0]['freshness'] == 'stale'
    assert value['checks'][0]['state'] == 'absent'


@pytest.mark.parametrize('moving', ['source', 'ledger', 'config', 'ref'])
def test_detected_changes_during_export_invalidate_association(project, monkeypatch, moving):
    from core.patchproof import report
    root, base, head = project
    ledger = seed(root)
    original = report.verification_report
    calls = []
    def change(*args, **kwargs):
        value = original(*args, **kwargs)
        if not calls:
            if moving == 'source':
                (root / 'service.py').write_bytes(b'value=5\n')
            elif moving == 'ledger':
                ledger.evidence[0].result = Result.FAIL
                ledger.save()
            elif moving == 'config':
                (root / '.elevenpowers/config.json').write_text('{"auto_detect":false}')
            else:
                (root / 'service.py').write_bytes(b'value=4\n')
                commit(root, 'moving ref')
            calls.append(True)
        return value
    monkeypatch.setattr(report, 'verification_report', change)
    value = report.build(root, base, 'HEAD')
    assert value['binding']['state'] == 'unavailable'
    assert value['binding']['issues']
    assert value['receipts'][0]['association'] == 'unavailable'


def test_partial_report_or_exhausted_deadline_never_bind(project):
    from core.patchproof.report import build
    root, base, head = project
    seed(root)
    value = build(root, base, head, timeout=0)
    assert value['binding']['state'] == 'unavailable'
    assert value['binding']['issues']


def test_bundle_excludes_private_text_and_raw_changes(project):
    from core.patchproof.report import build
    root, base, head = project
    token = 'ghp_' + 'A' * 30
    seed(root, command=f'check --token={token}')
    text = json.dumps(build(root, base, head))
    assert token not in text
    assert 'private prompt' not in text and 'private receipt detail' not in text
    assert 'value=2' not in text and str(root) not in text

