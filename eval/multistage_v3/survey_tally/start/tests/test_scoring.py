import pytest

from surveytally.files.survey_file import survey_from_dict
from surveytally.model.errors import ScoringError
from surveytally.model.responses import Response
from surveytally.services.scoring import check_definitions, compute_scores

from conftest import CUSTOMER


@pytest.fixture
def responses():
    return [
        Response('R1', {'satisfaction': 5, 'ease': 4, 'recommend': 10}),
        Response('R2', {'satisfaction': 2, 'ease': 3, 'recommend': 6}),
        Response('R3', {'satisfaction': 4, 'recommend': 8}),
        Response('R4', {'comments': 'no scores'}),
    ]


def test_mean_uses_the_answered_items(customer_survey, responses):
    overall = compute_scores(customer_survey, responses)['overall']
    assert overall.values == {'R1': 4.5, 'R2': 2.5, 'R3': 4.0, 'R4': None}
    assert overall.mean == pytest.approx(11 / 3)
    assert overall.base == 3


def test_top_box_is_a_share_of_items(customer_survey, responses):
    happy = compute_scores(customer_survey, responses)['happy']
    assert happy.values['R1'] == 1.0
    assert happy.values['R2'] == 0.0
    assert happy.values['R3'] == 1.0


def test_nps_classifies_promoters_and_detractors(customer_survey, responses):
    nps = compute_scores(customer_survey, responses)['nps']
    assert [nps.values[r] for r in ('R1', 'R2', 'R3')] == [100.0, -100.0, 0.0]
    assert nps.mean == 0.0


def test_weights_shift_the_mean(customer_survey, responses):
    weights = {'R1': 3.0, 'R2': 1.0, 'R3': 1.0, 'R4': 1.0}
    nps = compute_scores(customer_survey, responses, weights)['nps']
    assert nps.mean == pytest.approx(40.0)


def test_unknown_rules_are_reported():
    survey = survey_from_dict({**CUSTOMER, 'scores': [{'name': 'x', 'rule': 'median', 'items': ['ease']}]})
    assert check_definitions(survey) == ['unknown scoring rule median']
    with pytest.raises(ScoringError, match='unknown scoring rule median'):
        compute_scores(survey, [])


def test_scores_need_scale_questions():
    survey = survey_from_dict({**CUSTOMER, 'scores': [{'name': 'x', 'rule': 'sum', 'items': ['contact']}]})
    assert check_definitions(survey) == ['score x: contact is not a scale question']
