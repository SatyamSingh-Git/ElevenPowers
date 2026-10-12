"""Planning preserves declared coverage and does not execute project code."""
import json

from core.config import Config, save
from core.evidence import Result
from tests.test_patchproof_report import project, seed


def files(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*')
            if p.is_file() and '.git' not in p.relative_to(root).parts}


def test_plan_is_read_only_and_preserves_every_command(project):
    from core.patchproof.planning import plan
    root, base, head = project
    save(root, Config(auto_detect=False, commands={'tests': 'echo never-run',
        'build': 'echo never-run', 'custom': 'echo unknown'}))
    before = files(root)
    value = plan(root, base, head, seconds=20, command_seconds=3)
    assert files(root) == before
    assert value['kind'] == 'patchproof_plan'
    assert value['ready'] is False  # Unknown property must not disappear.
    assert len(value['checks']) == 2
    assert value['checks'][0]['properties'] == ['tests', 'build']
    assert value['checks'][0]['required'] is True
    assert value['checks'][0]['state'] == 'absent'
    assert value['checks'][1]['supported'] is False
    assert value['budgets']['seconds'] == 20
    assert value['budgets']['command_seconds'] == 3
    assert value['estimated_seconds'] is None


def test_latest_failure_remains_planned_even_after_a_success(project):
    from core.patchproof.planning import plan
    root, base, head = project
    save(root, Config(auto_detect=False, commands={'tests': 'echo check'}))
    ledger = seed(root, declaration='tests', command='echo check')
    old = ledger.evidence[0]
    from dataclasses import replace
    ledger.add([replace(old, result=Result.FAIL, at=old.at + 1)])
    ledger.save()
    value = plan(root, base, head)
    assert value['ready'] is True
    assert value['checks'][0]['state'] == 'failed'
    assert value['checks'][0]['action'] == 'run'


def test_dirty_patch_refuses_execution_but_keeps_check_visible(project):
    from core.patchproof.planning import plan
    root, base, head = project
    save(root, Config(auto_detect=False, commands={'tests': 'echo check'}))
    (root / 'service.py').write_text('broken = True')
    value = plan(root, base, head)
    assert value['ready'] is False
    assert value['checks'][0]['required'] is True
    assert value['issues']


def test_declaration_limit_is_explicit_not_silently_truncated(project):
    from core.patchproof.planning import plan
    root, base, head = project
    save(root, Config(auto_detect=False, commands={f'custom{i}': 'echo check' for i in range(65)}))
    value = plan(root, base, head)
    assert value['ready'] is False
    assert value['omitted_declarations'] == 1
    assert any('limit' in issue for issue in value['issues'])


def test_off_profile_plan_still_explains_checks(project):
    from core.patchproof.planning import plan
    root, base, head = project
    save(root, Config(profile='off', auto_detect=False, commands={'tests': 'echo check'}))
    value = plan(root, base, head)
    assert value['ready'] is False
    assert value['checks'][0]['required'] is True
    assert any('off' in issue for issue in value['issues'])


def test_current_legacy_receipt_is_not_reuse_provenance(project):
    from core.patchproof.planning import plan
    root, base, head = project
    save(root, Config(auto_detect=False, commands={'tests': 'echo check'}))
    seed(root, declaration='tests', command='echo check')
    value = plan(root, base, head)
    assert value['checks'][0]['state'] == 'current'
    assert value['checks'][0]['action'] == 'run'
