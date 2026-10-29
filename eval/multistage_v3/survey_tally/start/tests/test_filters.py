import pytest

from surveytally.model.errors import SurveyError
from surveytally.model.responses import Response
from surveytally.services.filters import parse_condition, select

RESPONSES = [
    Response('R1', {'region': 'north', 'channels': ('web', 'app'), 'ease': 5}),
    Response('R2', {'region': 'south', 'channels': ('store',), 'ease': 2, 'comments': 'Too slow'}),
    Response('R3', {'region': 'east'}),
]


def matching(survey, *conditions):
    return [response.respondent for response in select(RESPONSES, [parse_condition(survey, c) for c in conditions])]


def test_choice_conditions(poll_survey):
    assert matching(poll_survey, 'region=north,east') == ['R1', 'R3']
    assert matching(poll_survey, 'region!=north') == ['R2', 'R3']
    assert matching(poll_survey, 'channels=app') == ['R1']


def test_scale_conditions_compare_numbers(customer_survey):
    assert matching(customer_survey, 'ease>=3') == ['R1']
    assert matching(customer_survey, 'ease<5') == ['R2']


def test_answered_condition(poll_survey):
    assert matching(poll_survey, 'comments?') == ['R2']


def test_conditions_combine(customer_survey):
    assert matching(customer_survey, 'ease?', 'channels!=store') == ['R1']


@pytest.mark.parametrize('text, message', [
    ('region=mars', 'has no option mars'),
    ('region>north', 'only support = and !='),
    ('ease=ten', 'compares with whole numbers'),
    ('ease>=9', '9 is outside 1..5'),
    ('comments=x', 'free-text questions only support ?'),
    ('region', 'cannot read the condition'),
])
def test_bad_conditions(poll_survey, customer_survey, text, message):
    survey = customer_survey if text.startswith(('ease', 'comments')) else poll_survey
    with pytest.raises(SurveyError, match=message):
        parse_condition(survey, text)
