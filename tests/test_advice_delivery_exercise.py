"""Actual commands and synthetic launcher ingress; no model sessions."""
from pathlib import Path
import shutil

import pytest


@pytest.mark.parametrize('language', ['python', 'javascript'])
def test_actual_producer_keeps_replay_and_native_ingress_distinct(tmp_path, language):
    from eval.advice_delivery import exercise
    if language == 'javascript' and not shutil.which('node'):
        pytest.skip('Node unavailable')
    value = exercise(tmp_path / 'new', languages=(language,), hosts=('claude',))
    assert value['qualified']
    assert value['model_calls'] == 0 and value['installed_acceptance'] is False
    assert len(value['observations']) == 2
    native = next(row for row in value['observations'] if row['mode'] == 'native-control')
    replay = next(row for row in value['observations'] if row['mode'] == 'replay')
    assert native['followups'] == ['current', 'failed', 'incomplete', 'current']
    assert native['before_check']['matching_native_receipts'] == 0
    assert replay['before_check']['state'] == 'generated'
    assert all(row == 'unobserved' for row in replay['followups'])


def test_producer_refuses_existing_destination_without_changing_it(tmp_path):
    from eval.advice_delivery import exercise
    marker = tmp_path / 'keep.txt'
    marker.write_text('keep')
    with pytest.raises(ValueError, match='new'):
        exercise(tmp_path)
    assert marker.read_text() == 'keep'
