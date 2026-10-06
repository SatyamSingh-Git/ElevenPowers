import shutil

import pytest


def test_staged_exercise_rejects_fault_accepts_repair_and_retains_history(tmp_path):
    from eval.milestones import exercise
    result = exercise(tmp_path / 'exercise')
    assert result['fault']['exit_code'] != 0
    assert result['repair']['exit_code'] == 0
    assert result['equivalent']['exit_code'] == 0
    assert result['new_task_kept_evidence']
    assert result['after_edit']['state'] == 'STALE'
    assert result['after_failed_refresh']['state'] == 'FAILED'
    assert result['after_repair']['state'] == 'CURRENT'
    assert result['scoped_unrelated']['state'] == 'CURRENT'
    assert result['qualified']
    if shutil.which('node'):
        assert result['node']['qualified']
        assert result['node']['fault']['exit_code'] != 0
        assert result['node']['after_repair']['state'] == 'CURRENT'
    else:
        assert result['node']['state'] == 'unavailable'


def test_exercise_refuses_existing_destination_before_mutating_it(tmp_path):
    from eval.milestones import exercise
    before = tmp_path / 'keep.txt'; before.write_text('preserve')
    with pytest.raises(ValueError):
        exercise(tmp_path)
    assert before.read_text() == 'preserve'
