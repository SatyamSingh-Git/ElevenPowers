"""Independent actual-command rehearsal of informational GitHub presentation."""
import hashlib


def test_rehearsal_distinguishes_actual_pass_failure_and_incomplete_without_rerun(tmp_path):
    from eval.github_presentation import prepare
    from core.patchproof.github import canonical
    result = prepare(tmp_path / 'new')
    assert result['states'] == ['current', 'failed', 'incomplete']
    assert result['readonly'] is True
    assert result['counts'] == [1, 1, 1]
    assert result['passing']['bundle_sha256'] == hashlib.sha256(canonical(result['passing']['bundle'])).hexdigest()
    assert result['passing']['bundle']['checks'][1]['state'] == 'absent'
