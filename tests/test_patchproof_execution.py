"""Actual commands verify behavior, durable interruptions and qualified reuse."""
import json
import shutil
import sys
import time

import pytest

from core.config import Config, save
from core.ledger import Ledger
from tests.test_patchproof_identity import commit, git


@pytest.fixture
def runnable(tmp_path):
    git(tmp_path, 'init', '-q')
    git(tmp_path, 'config', 'core.autocrlf', 'false')
    Ledger(root=tmp_path).save()  # Ordinary project setup excludes runtime state.
    (tmp_path / 'service.py').write_bytes(b'value=1\n')
    (tmp_path / 'check.py').write_text(
        "from pathlib import Path\nimport service\n"
        "p=Path('.elevenpowers/count.txt')\n"
        "p.write_text(str(int(p.read_text())+1) if p.exists() else '1')\n"
        "assert service.value == 2, 'independent expected value'\n"
        "print('verified actual behavior')\n", encoding='utf-8')
    base = commit(tmp_path, 'base')
    (tmp_path / 'service.py').write_bytes(b'value=2\n')
    head = commit(tmp_path, 'change')
    command = f'"{sys.executable}" -B check.py'
    save(tmp_path, Config(auto_detect=False, commands={'tests': command}))
    return tmp_path, base, head, command


def test_explicit_execution_collects_receipts_and_reuses_only_fresh_results(runnable):
    from core.patchproof.execution import verify
    from core.patchproof.report import build
    root, base, head, command = runnable
    first = verify(root, base, head, seconds=120, command_seconds=5)
    assert first['state'] == 'passed', first
    assert first['checks'][0]['status'] == 'passed'
    assert (root / '.elevenpowers/count.txt').read_text() == '1'
    second = verify(root, base, head, seconds=120, command_seconds=5)
    assert second['state'] == 'passed', second
    assert second['checks'][0]['status'] == 'reused'
    assert (root / '.elevenpowers/count.txt').read_text() == '1'
    bundle = build(root, base, head)
    assert bundle['execution']['checks'][0]['association'] == 'bound'
    assert bundle['execution']['checks'][0]['executed_at_patch_head'] == head
    assert bundle['checks'][0]['state'] == 'current'


def test_new_fault_is_detected_by_independent_actual_check(runnable):
    from core.patchproof.execution import verify
    root, base, head, command = runnable
    (root / 'service.py').write_bytes(b'value=9\n')
    faulty = commit(root, 'fault')
    value = verify(root, base, faulty, seconds=120, command_seconds=5)
    assert value['state'] == 'failed'
    records = Ledger.load(root).evidence
    assert records[-1].execution == 'complete'
    assert records[-1].result.value == 'fail'


def test_timeout_keeps_incomplete_receipt_and_never_reuses_old_pass(runnable):
    from core.patchproof.execution import verify
    root, base, head, command = runnable
    assert verify(root, base, head, seconds=120)['state'] == 'passed'
    save(root, Config(auto_detect=False, commands={'tests': f'"{sys.executable}" -c "import time; time.sleep(60)"'}))
    value = verify(root, base, head, seconds=120, command_seconds=.15)
    assert value['state'] == 'incomplete'
    assert value['checks'][0]['status'] == 'incomplete'
    assert Ledger.load(root).evidence[-1].execution == 'incomplete'


def test_source_changed_by_command_stops_later_required_checks(runnable):
    from core.patchproof.execution import verify
    root, base, head, command = runnable
    (root / 'change.py').write_text("from pathlib import Path\nPath('service.py').write_text('value=99\\n')\n")
    head = commit(root, 'declare changing command')
    save(root, Config(auto_detect=False, commands={'tests': f'"{sys.executable}" change.py',
        'build': f'"{sys.executable}" -c "from pathlib import Path; Path(\'.elevenpowers/later\').touch()"'}))
    value = verify(root, base, head, seconds=120)
    assert value['state'] == 'incomplete'
    assert value['checks'][0]['status'] == 'stale'
    assert not (root / '.elevenpowers/later').exists()
    assert value['checks'][1]['status'] == 'deferred'


@pytest.mark.parametrize('reason', ['dirty', 'off', 'budget'])
def test_unqualified_or_passive_attempt_never_launches(runnable, reason):
    from core.patchproof.execution import verify
    root, base, head, command = runnable
    if reason == 'dirty':
        (root / 'service.py').write_bytes(b'value=100\n')
    if reason == 'off':
        save(root, Config(profile='off', auto_detect=False, commands={'tests': command}))
    value = verify(root, base, head, seconds=0 if reason == 'budget' else 30)
    assert value['state'] == 'incomplete'
    assert not (root / '.elevenpowers/count.txt').exists()


def test_duplicate_supported_declarations_share_one_actual_execution(runnable):
    from core.patchproof.execution import verify
    root, base, head, command = runnable
    save(root, Config(auto_detect=False, commands={'tests': command, 'build': command}))
    value = verify(root, base, head, seconds=120)
    assert value['state'] == 'passed', value
    assert (root / '.elevenpowers/count.txt').read_text() == '1'
    assert {e.declaration for e in Ledger.load(root).evidence} == {'tests', 'build'}


def test_ignored_configuration_change_expires_execution_reuse(runnable):
    from core.patchproof.execution import verify
    root, base, head, command = runnable
    assert verify(root, base, head, seconds=120)['state'] == 'passed'
    path = root / '.elevenpowers/config.json'
    raw = json.loads(path.read_text()); raw['extra_policy'] = True
    path.write_text(json.dumps(raw))
    assert verify(root, base, head, seconds=120)['state'] == 'passed'
    assert (root / '.elevenpowers/count.txt').read_text() == '2'


def test_saved_state_cannot_promote_a_later_legacy_failure(runnable):
    from core.patchproof.execution import verify
    from core.patchproof.planning import plan
    from core.parsers import parse
    root, base, head, command = runnable
    assert verify(root, base, head, seconds=120)['state'] == 'passed'
    ledger = Ledger.load(root)
    ledger.add(parse(command, 'failure', 1, root))
    ledger.save()
    value = plan(root, base, head, seconds=120)
    assert value['checks'][0]['state'] == 'failed'
    assert value['checks'][0]['action'] == 'run'


def test_actual_javascript_declared_suite(tmp_path):
    from core.patchproof.execution import verify
    node = shutil.which('node')
    if not node:
        pytest.skip('Node unavailable')
    git(tmp_path, 'init', '-q'); git(tmp_path, 'config', 'core.autocrlf', 'false')
    Ledger(root=tmp_path).save()
    (tmp_path / 'service.js').write_bytes(b'module.exports = 1;\n')
    (tmp_path / 'service.test.js').write_text(
        "const test=require('node:test'); const assert=require('node:assert/strict');\n"
        "test('independent expected behavior',()=>assert.equal(require('./service'),2));\n")
    base = commit(tmp_path, 'base')
    (tmp_path / 'service.js').write_bytes(b'module.exports = 2;\n')
    head = commit(tmp_path, 'change')
    save(tmp_path, Config(auto_detect=False, commands={'tests': f'"{node}" --test service.test.js'}))
    value = verify(tmp_path, base, head, seconds=120)
    assert value['state'] == 'passed', value
    assert Ledger.load(tmp_path).evidence[-1].passed == 1
    (tmp_path / 'service.js').write_bytes(b'module.exports = 5;\n')
    faulty = commit(tmp_path, 'fault')
    value = verify(tmp_path, base, faulty, seconds=120)
    assert value['state'] == 'failed'
    assert Ledger.load(tmp_path).evidence[-1].failed == 1


@pytest.mark.parametrize('raw', ['{broken', '{"schema":1,"schema":1,"attempts":[],"evicted":0}', '[' * 1500 + '0' + ']' * 1500], ids=['malformed', 'duplicate', 'deep'])
def test_damaged_saved_state_is_controlled_and_never_launches(runnable, raw):
    from core.patchproof.execution import verify
    from core.patchproof.planning import plan
    root, base, head, _ = runnable
    (root / '.elevenpowers/patch-verification.json').write_text(raw)
    value = plan(root, base, head, seconds=120)
    assert value['ready'] is False
    assert value['bundle']['execution']['state'] == 'incomplete'
    assert verify(root, base, head, seconds=120)['state'] == 'incomplete'
    assert not (root / '.elevenpowers/count.txt').exists()


def test_changed_environment_invalidates_reuse(runnable, monkeypatch):
    from core.patchproof.execution import verify
    root, base, head, _ = runnable
    assert verify(root, base, head, seconds=120)['state'] == 'passed'
    monkeypatch.setenv('EP_EXECUTION_CONTROL', 'changed')
    value = verify(root, base, head, seconds=120)
    assert value['state'] == 'passed'
    assert value['checks'][0]['status'] == 'passed'
    assert (root / '.elevenpowers/count.txt').read_text() == '2'


def test_output_limit_is_incomplete_not_passing(runnable):
    from core.patchproof.execution import verify
    root, base, head, _ = runnable
    save(root, Config(auto_detect=False, commands={'tests':
        f'"{sys.executable}" -c "import os; os.write(1,b\'x\'*(9*1024*1024))"'}))
    value = verify(root, base, head, seconds=120, command_seconds=5)
    assert value['state'] == 'incomplete'
    assert value['checks'][0]['status'] == 'incomplete'
    assert Ledger.load(root).evidence[-1].execution == 'incomplete'


def test_final_environment_drift_cannot_report_qualified_success(runnable, monkeypatch):
    from core.patchproof import execution
    root, base, head, _ = runnable
    original = execution.build
    def moving(*args, **kwargs):
        monkeypatch.setenv('EP_FINAL_INSPECTION_CONTROL', 'changed after command')
        return original(*args, **kwargs)
    monkeypatch.setattr(execution, 'build', moving)
    value = execution.verify(root, base, head, seconds=120)
    assert value['bundle']['binding']['state'] == 'bound'
    assert value['bundle']['execution']['checks'][0]['association'] == 'unavailable'
    assert value['state'] == 'incomplete'


def test_actual_zero_executed_tests_is_incomplete_not_a_failed_assertion(runnable):
    from core.patchproof.execution import verify
    node = shutil.which('node')
    if not node:
        pytest.skip('Node unavailable')
    root, base, head, _ = runnable
    (root / 'skip.test.js').write_text("const test=require('node:test'); test('skipped',{skip:true},()=>{});\n")
    head = commit(root, 'skipped control')
    save(root, Config(auto_detect=False, commands={'tests': f'"{node}" --test skip.test.js'}))
    value = verify(root, base, head, seconds=120)
    assert value['state'] == 'incomplete'
    assert value['bundle']['checks'][0]['state'] == 'no_tests'


def test_empty_pair_retains_execution_identity_without_inventing_changed_paths(runnable):
    from core.patchproof.execution import verify
    root, _, head, _ = runnable
    value = verify(root, head, head, seconds=120)
    assert value['state'] == 'passed'
    assert value['bundle']['patch']['empty'] is True
    assert value['bundle']['receipts'][-1]['patch_paths'] == []
    assert value['bundle']['execution']['checks'][0]['executed_at_patch_head'] == head


def test_explicit_rerun_can_refresh_unobserved_external_inputs(runnable):
    from core.patchproof.execution import verify
    root, base, head, _ = runnable
    assert verify(root, base, head, seconds=120)['state'] == 'passed'
    value = verify(root, base, head, seconds=120, reuse=False)
    assert value['state'] == 'passed'
    assert value['checks'][0]['status'] == 'passed'
    assert (root / '.elevenpowers/count.txt').read_text() == '2'


def test_execution_state_moving_during_inspection_cannot_keep_old_success(runnable, monkeypatch):
    from core.patchproof.execution import verify
    from core.patchproof.report import build
    from core.patchproof import execution_report, execution_state
    root, base, head, _ = runnable
    assert verify(root, base, head, seconds=120)['state'] == 'passed'
    original = execution_report.witness
    def moving(*args, **kwargs):
        value = original(*args, **kwargs)
        saved = execution_state.read(root)
        saved['attempts'][-1]['status'] = 'incomplete'
        execution_state.save(root, saved)
        return value
    monkeypatch.setattr(execution_report, 'witness', moving)
    value = build(root, base, head)
    assert value['execution']['state'] == 'incomplete'
    assert not any(c['association'] == 'bound' for c in value['execution']['checks'])
