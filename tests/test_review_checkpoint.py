"""Fixed-patch review must preserve the starting code and existing checks."""
import importlib.util
import subprocess

import pytest


def test_checkpoint_review_flow_exists():
    assert importlib.util.find_spec('eval.review_checkpoint'), 'fixed-patch review flow is missing'


def _case(tmp_path):
    repo = tmp_path / 'repo'
    repo.mkdir()
    (repo / 'logic.py').write_text('def value(): return 1\n')
    (repo / 'tests').mkdir()
    (repo / 'tests/test_logic.py').write_text('def test_value():\n    from logic import value\n    assert value() == 1\n')
    for args in [('init', '-q'), ('add', '.'), ('-c', 'user.name=Review', '-c', 'user.email=review@example.invalid', 'commit', '-qm', 'base')]:
        subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True)
    base = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD']).decode().strip()
    case = {'id': 'case-one', 'repository': str(repo), 'base': base, 'patch': '', 'environment': {}, 'source_paths': ['logic.py']}
    return case


def test_prepare_uses_frozen_patch_and_refuses_reuse(tmp_path):
    from eval.review_checkpoint import prepare, seal
    case = _case(tmp_path)
    root = tmp_path / 'candidate'
    frozen = prepare(case, root)
    assert frozen == seal(root)
    (root / 'tests/test_added.py').write_text('def test_more(): assert True\n')
    assert frozen == seal(root)
    (root / 'logic.py').write_text('def value(): return 2\n')
    assert frozen != seal(root)
    with pytest.raises(ValueError):
        prepare(case, root)


def test_visible_failure_and_no_tests_are_not_success(tmp_path):
    from eval.review_checkpoint import execute_tests
    import sys
    root = tmp_path / 'candidate'
    root.mkdir()
    (root / 'test_bad.py').write_text('def test_bad(): assert False\n')
    failed = execute_tests(root, [sys.executable, '-m', 'pytest', '-q'], seconds=20)
    assert failed['state'] == 'failed' and failed['failed'] == 1
    (root / 'test_bad.py').unlink()
    empty = execute_tests(root, [sys.executable, '-m', 'pytest', '-q'], seconds=20)
    assert empty['state'] == 'empty' and empty['passed'] == 0


def test_feedback_omits_mutation_targets_and_keeps_incomplete_qualification(tmp_path):
    from eval.review_checkpoint import review_brief
    (tmp_path / 'logic.py').write_text('def apply(value):\n    return value > 0\n')
    record = {'state': 'incomplete', 'issues': ['attempt budget exhausted'], 'observations': [
        {'path': 'logic.py', 'line': 2, 'operator': 'ChangeComparisonOperator', 'id': 'secret-target', 'status': 'undetected'},
        {'path': 'logic.py', 'line': 1, 'operator': 'DeleteStatement', 'id': 'other', 'status': 'timed_out'},
    ]}
    text = review_brief(tmp_path, record)
    assert 'apply' in text and 'incomplete' in text and 'equivalent' in text
    assert 'secret-target' not in text and 'ChangeComparisonOperator' not in text
    assert 'DeleteStatement' not in text and 'value > 0' not in text
def test_capture_additions_enforces_existing_inputs_and_size(tmp_path):
    from eval.review_checkpoint import prepare, capture_additions
    case = _case(tmp_path)
    root = tmp_path/'candidate'
    expected = prepare(case, root)
    (root/'tests/test_extra.py').write_text('def test_extra():\n    assert True\n')
    assert capture_additions(root, expected) == {'tests/test_extra.py':'def test_extra():\n    assert True\n'}
    (root/'tests/test_extra.py').write_text('x'*(1024*1024+1))
    with pytest.raises(ValueError, match='limit'):
        capture_additions(root, expected)
    (root/'tests/test_extra.py').write_text('def test_extra():\n    assert True\n')
    (root/'logic.py').write_text('corrupted')
    with pytest.raises(ValueError, match='protected'):
        capture_additions(root, expected)


def test_execution_unavailable_is_explicit(tmp_path):
    from eval.review_checkpoint import execute_tests
    result=execute_tests(tmp_path, ['ep-no-such-executable'])
    assert result['state']=='unavailable' and result['passed']==0
