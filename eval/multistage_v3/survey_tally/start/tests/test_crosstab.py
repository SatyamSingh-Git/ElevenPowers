import pytest

from surveytally.model.errors import SurveyError
from surveytally.model.responses import Response
from surveytally.reports.tables import crosstab_table
from surveytally.services.crosstab import crosstab
from surveytally.services.significance import significance, z_score


@pytest.fixture
def responses():
    return [
        Response('R1', {'region': 'north', 'contact': 'phone'}),
        Response('R2', {'region': 'north', 'contact': 'email'}),
        Response('R3', {'region': 'south', 'contact': 'email'}),
        Response('R4', {'region': 'south', 'contact': 'email'}),
        Response('R5', {'region': 'east'}),
    ]


def test_column_percentages(poll_survey, responses):
    tab = crosstab(poll_survey, responses, 'region', 'contact')
    assert tab.column_bases == {'phone': 1.0, 'email': 3.0}
    assert tab.percent('north', 'phone') == 100.0
    assert tab.percent('south', 'email') == pytest.approx(200 / 3)
    assert tab.total_percent('north') == 50.0


def test_crosstab_table_ends_with_bases(poll_survey, responses):
    table = crosstab_table(crosstab(poll_survey, responses, 'region', 'contact'))
    assert table.columns == ['region', 'Phone', 'Email', 'Total']
    assert table.rows[-1] == ['n', '1', '3', '4']


def test_a_question_cannot_be_crossed_with_itself(poll_survey, responses):
    with pytest.raises(SurveyError):
        crosstab(poll_survey, responses, 'region', 'region')


def test_significance_marks_the_higher_column(poll_survey):
    responses = ([Response(f'A{n}', {'region': 'north', 'contact': 'phone'}) for n in range(40)]
                 + [Response(f'B{n}', {'region': 'north' if n < 10 else 'south', 'contact': 'email'})
                    for n in range(40)])
    marks = significance(crosstab(poll_survey, responses, 'region', 'contact'))
    assert marks[('north', 'phone')] == 'B'
    assert marks[('north', 'email')] == ''
    assert z_score(10, 40, 10, 40) == 0.0
