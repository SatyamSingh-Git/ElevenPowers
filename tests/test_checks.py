"""Owned exact commands, tested against real processes and persisted receipts."""
import json
import math
import sys
from pathlib import Path

import pytest

from core.config import Config, save
from core.evidence import Freshness, Result
from core.jobs import Session
from core.ledger import Ledger


def project(root, body="print('TAP version 13\\n1..1\\nok 1 - check\\n# tests 1\\n# pass 1\\n# fail 0')"):
    root.mkdir(parents=True, exist_ok=True)
    script = root / 'check.py'
    script.write_text("from pathlib import Path\n" + body + '\n', encoding='utf8')
    command = f'"{sys.executable}" check.py'
    save(root, Config(profile='guide', commands={'tests': command}, auto_detect=False))
    if not (root / '.elevenpowers/ledger.json').exists():
        Ledger(root=root, task='original-task').save()
    return command


def aggregate(root):
    return [e for e in Ledger.load(root).evidence if e.declaration == 'tests' and e.kind.value == 'test_suite'][-1]


def test_actual_pass_failure_and_repair(tmp_path):
    from core.checks import execute
    project(tmp_path)
    assert execute(tmp_path, 'tests')['state'] == 'passed'
    project(tmp_path, "print('not ok 1 - broken'); raise SystemExit(1)")
    failed = execute(tmp_path, 'tests')
    assert (failed['state'], failed['exit_code']) == ('failed', 1)
    assert aggregate(tmp_path).result is Result.FAIL
    project(tmp_path)
    assert execute(tmp_path, 'tests')['state'] == 'passed'
    assert aggregate(tmp_path).freshness(tmp_path) is Freshness.FRESH


def test_timeout_supersedes_old_pass_with_incomplete(tmp_path):
    from core.checks import execute
    project(tmp_path)
    assert execute(tmp_path, 'tests')['state'] == 'passed'
    project(tmp_path, 'import time; time.sleep(10)')
    result = execute(tmp_path, 'tests', seconds=.1)
    assert result['state'] == 'incomplete' and result['exit_code'] is None
    assert aggregate(tmp_path).execution == 'incomplete'


@pytest.mark.parametrize('seconds', [0, -1, math.inf, math.nan, 601, True])
def test_invalid_budget_launches_nothing(tmp_path, seconds):
    from core.checks import execute
    project(tmp_path, "Path('launched').write_text('bad')")
    with pytest.raises(ValueError):
        execute(tmp_path, 'tests', seconds=seconds)
    assert not (tmp_path / 'launched').exists()


@pytest.mark.parametrize('mode', ['unknown', 'off', 'busy'])
def test_refusal_launches_nothing(tmp_path, mode):
    from core.checks import execute
    command = project(tmp_path, "Path('launched').write_text('bad')")
    if mode == 'off':
        save(tmp_path, Config(profile='off', commands={'tests': command}))
    if mode == 'busy':
        with Session(tmp_path, 'original-task'):
            result = execute(tmp_path, 'tests')
    else:
        result = execute(tmp_path, 'unknown' if mode == 'unknown' else 'tests')
    assert result['state'] == 'incomplete'
    assert not (tmp_path / 'launched').exists()


@pytest.mark.parametrize('change', ['source', 'configuration', 'task'])
def test_actual_mid_execution_movement_prevents_current_pass(tmp_path, change):
    from core.checks import execute
    statements = {
        'source': "Path('new.py').write_text('new = True')",
        'configuration': "import json; p=Path('.elevenpowers/config.json'); v=json.loads(p.read_text()); v['profile']='strict'; p.write_text(json.dumps(v))",
        'task': "import json; p=Path('.elevenpowers/ledger.json'); v=json.loads(p.read_text()); v['task']='replacement'; p.write_text(json.dumps(v))",
    }
    project(tmp_path, statements[change] + "\nprint('ok 1 - check')")
    result = execute(tmp_path, 'tests')
    assert result['state'] == 'incomplete'
    if change == 'task':
        assert Ledger.load(tmp_path).task == 'replacement'
        assert aggregate(tmp_path).execution == 'incomplete'
    else:
        assert aggregate(tmp_path).freshness(tmp_path) is not Freshness.FRESH


def test_runtime_movement_prevents_pass(tmp_path, monkeypatch):
    import core.hosts.provenance as provenance
    from core.checks import execute
    project(tmp_path)
    original = provenance.fingerprint
    count = 0
    def moving(*args, **kwargs):
        nonlocal count
        count += 1
        return original(*args, **kwargs) if count == 1 else 'f' * 64
    monkeypatch.setattr(provenance, 'fingerprint', moving)
    assert execute(tmp_path, 'tests')['state'] == 'incomplete'
    assert aggregate(tmp_path).freshness(tmp_path) is Freshness.STALE


def test_configuration_change_after_pass_expires_owned_evidence(tmp_path):
    from core.checks import execute
    command = project(tmp_path)
    assert execute(tmp_path, 'tests')['state'] == 'passed'
    save(tmp_path, Config(profile='strict', commands={'tests': command}, auto_detect=False))
    assert aggregate(tmp_path).freshness(tmp_path) is Freshness.STALE


def test_unknown_listing_is_read_only(tmp_path):
    from core.checks import available
    (tmp_path / 'package.json').write_text(json.dumps({'scripts': {'ci': 'node check.mjs'}}))
    assert available(tmp_path)['commands'] == {'tests': 'npm run ci'}
    assert not (tmp_path / '.elevenpowers').exists()


def test_aliases_receive_exact_declared_receipts(tmp_path):
    from core.checks import execute
    command = project(tmp_path)
    save(tmp_path, Config(profile='guide', commands={'tests': command, 'build': command}, auto_detect=False))
    assert execute(tmp_path, 'tests')['state'] == 'passed'
    assert {e.declaration for e in Ledger.load(tmp_path).evidence} == {'tests', 'build'}
