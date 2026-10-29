import pytest

from surveytally.model.errors import WeightingError
from surveytally.model.responses import Response
from surveytally.services.weighting import compute_weights, describe, efficiency, weight_for


def regions(*codes):
    return [Response(f'R{index}', {'region': code}) for index, code in enumerate(codes, start=1)]


def test_one_question_gives_cell_weights(poll_survey):
    responses = regions('north', 'north', 'north', 'south')
    weights = compute_weights(poll_survey, responses, {'region': {'north': 0.5, 'south': 0.5}})
    assert weights == {'R1': pytest.approx(2 / 3, abs=1e-6), 'R2': pytest.approx(2 / 3, abs=1e-6),
                       'R3': pytest.approx(2 / 3, abs=1e-6), 'R4': 2.0}


def test_two_questions_are_raked_until_both_match(poll_survey):
    responses = [
        Response('R1', {'region': 'north', 'contact': 'phone'}),
        Response('R2', {'region': 'north', 'contact': 'email'}),
        Response('R3', {'region': 'south', 'contact': 'email'}),
        Response('R4', {'region': 'south', 'contact': 'email'}),
    ]
    targets = {'region': {'north': 0.5, 'south': 0.5}, 'contact': {'phone': 0.4, 'email': 0.6}}
    weights = compute_weights(poll_survey, responses, targets)
    total = sum(weights.values())
    assert weights['R1'] / total == pytest.approx(0.4, abs=1e-4)
    assert (weights['R1'] + weights['R2']) / total == pytest.approx(0.5, abs=1e-4)


def test_weighting_needs_a_respondent_in_every_targeted_cell(poll_survey):
    with pytest.raises(WeightingError, match='no respondents chose south'):
        compute_weights(poll_survey, regions('north', 'north'), {'region': {'north': 0.5, 'south': 0.5}})


def test_only_single_choice_questions_can_be_weighted(poll_survey):
    with pytest.raises(WeightingError, match='only single-choice questions'):
        compute_weights(poll_survey, regions('north'), {'channels': {'web': 1.0}})


def test_missing_weights_are_an_error():
    assert weight_for(None, 'R9') == 1.0
    with pytest.raises(WeightingError, match='no weight for respondent R9'):
        weight_for({'R1': 1.0}, 'R9')


def test_efficiency_and_summary():
    weights = {'R1': 1.0, 'R2': 1.0, 'R3': 2.0}
    assert efficiency(weights) == pytest.approx(16 / 18)
    found = describe(weights)
    assert (found.smallest, found.largest, found.trimmed) == (1.0, 2.0, 0)
    assert found.effective_size == pytest.approx(16 / 6)
