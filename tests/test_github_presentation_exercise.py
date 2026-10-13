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


def test_real_presentation_can_expose_declared_external_inputs_without_inventing_execution(tmp_path):
    from eval.github_presentation import prepare
    result = prepare(tmp_path/'new',external_inputs=True)
    value = result['passing']['bundle']
    assert result['counts'] == [1,1,1]
    assert value['external_inputs']['state'] == 'available'
    assert len(value['external_inputs']['witnesses']) == 1
    assert value['execution']['state'] == 'absent', 'fresh collection does not invent legacy execution association'
