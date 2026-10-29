import pytest

from surveytally.files.targets_file import read_targets
from surveytally.files.weights_file import read_weights, write_weights
from surveytally.model.errors import WeightingError


def test_weights_round_trip(tmp_path):
    path = tmp_path / 'weights.csv'
    write_weights({'R1': 1.5, 'R2': 0.333333333}, path)
    assert path.read_text(encoding='utf-8').splitlines() == ['respondent,weight', 'R1,1.500000', 'R2,0.333333']
    assert read_weights(path) == {'R1': 1.5, 'R2': 0.333333}


def test_weights_must_be_positive(write_file):
    path = write_file('weights.csv', 'respondent,weight\nR1,0\n')
    with pytest.raises(WeightingError, match='row 2: weight must be above 0'):
        read_weights(path)


def test_a_respondent_has_one_weight(write_file):
    path = write_file('weights.csv', 'respondent,weight\nR1,1\nR1,2\n')
    with pytest.raises(WeightingError, match='respondent R1 appears twice'):
        read_weights(path)


def test_targets_are_read_by_question(write_file):
    path = write_file('targets.csv', 'question,option,share\nregion,north,0.25\nregion,south,0.75\n')
    assert read_targets(path) == {'region': {'north': 0.25, 'south': 0.75}}


def test_target_shares_must_add_up(write_file):
    path = write_file('targets.csv', 'question,option,share\nregion,north,0.25\nregion,south,0.5\n')
    with pytest.raises(WeightingError, match='shares for region add up to 0.750, not 1'):
        read_targets(path)
