"""Actual local processes feed replay callbacks; never claim installed acceptance."""
import pytest


def test_real_shell_receipts_qualify_success_failure_and_wrong_directory(tmp_path):
    from eval.command_invocations import exercise
    result = exercise(tmp_path / 'new', languages=('python',), shells=('system',))
    assert result['qualified'] and result['model_calls'] == 0
    assert result['installed_acceptance'] is False
    assert {row['case'] for row in result['observations']} == {
        'direct', 'wrapped', 'failed', 'wrong_directory', 'interrupted', 'masked_failure'}
    assert all(row['qualified'] for row in result['observations'])
    assert all(row['native_activation_written'] is False for row in result['observations'])
    rows = {row['case']: row for row in result['observations']}
    assert rows['failed']['process_exit'] != 0
    assert rows['wrong_directory']['process_exit'] == 0
    assert rows['wrong_directory']['receipt_state'] == 'INCOMPLETE'
    assert rows['masked_failure']['process_exit'] == 0
    assert rows['masked_failure']['declared_receipts'] == 0


def test_existing_producer_destination_is_preserved(tmp_path):
    from eval.command_invocations import exercise
    marker = tmp_path / 'keep'; marker.write_text('existing')
    with pytest.raises(ValueError):
        exercise(tmp_path)
    assert marker.read_text() == 'existing'
