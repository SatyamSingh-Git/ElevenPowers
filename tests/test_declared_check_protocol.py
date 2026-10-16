"""Actual independent consumers, no model or installed-host acceptance."""
import shutil
import pytest


@pytest.mark.parametrize('language', ['python', 'javascript'])
def test_declared_runner_preserves_independent_scopes_and_owned_failure(tmp_path, language):
    if language == 'javascript' and not shutil.which('node'):
        pytest.skip('Node unavailable')
    from eval.declared_checks import case
    value = case(tmp_path / 'new', language)
    assert value['outcomes'] == ['passed', 'passed', 'failed', 'passed', 'incomplete']
    assert value['milestones_after_fault'] == ['STALE', 'CURRENT']
    assert value['milestones_after_failure'] == ['FAILED', 'CURRENT']
    assert value['milestones_after_repair'] == ['CURRENT', 'CURRENT']
    assert value['counts_before_missing'] == [3, 1]
    assert value['outer_shell_exit'] == 0
    assert value['owned_failure_survived_callbacks']
    assert value['synthetic_hosts'] == ['claude', 'codex', 'gemini', 'cursor', 'copilot']
