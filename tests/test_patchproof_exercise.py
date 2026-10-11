import shutil

import pytest


def test_actual_python_and_node_checks_retain_four_outcomes(tmp_path):
    """Fabricated passes or losing failed/incomplete/absent checks break this."""
    from eval.patchproof import exercise
    if not shutil.which('node'):
        pytest.skip('Node required for the unrelated JavaScript producer')
    result = exercise(tmp_path / 'exercise')
    assert result['model_calls'] == 0
    assert [p['language'] for p in result['projects']] == ['python', 'javascript']
    for project in result['projects']:
        assert project['states'] == ['current', 'failed', 'incomplete', 'absent']
        assert project['exit_codes'] == [0, 1, None]
        assert project['dirty_binding'] == 'unavailable'
        assert project['independent_head_matches']

