import pytest

from surveytally.model.responses import Response
from surveytally.services.tally import frequencies


@pytest.fixture
def responses():
    return [
        Response('R1', {'region': 'north', 'channels': ('web', 'app')}),
        Response('R2', {'region': 'south', 'channels': ('web',)}),
        Response('R3', {'region': 'north', 'comments': 'More branches please'}),
        Response('R4', {'channels': ('store',)}),
    ]


def test_single_choice_counts(poll_survey, responses):
    table = frequencies(poll_survey, responses)['region']
    assert (table.base, table.missing) == (3, 1)
    assert table.row('north').count == 2
    assert table.row('north').percent == pytest.approx(200 / 3)
    assert table.row('west').count == 0


def test_multiple_choice_percentages_are_of_respondents(poll_survey, responses):
    table = frequencies(poll_survey, responses)['channels']
    assert table.base == 3
    assert table.row('web').percent == pytest.approx(200 / 3)
    assert sum(row.percent for row in table.rows) > 100


def test_weighted_counts(poll_survey, responses):
    weights = {'R1': 0.5, 'R2': 2.0, 'R3': 0.5, 'R4': 1.0}
    table = frequencies(poll_survey, responses, weights)['region']
    assert table.row('north').count == 2
    assert table.row('north').weighted == 1.0
    assert table.row('south').percent == pytest.approx(200 / 3)


def test_free_text_counts_answers_only(poll_survey, responses):
    table = frequencies(poll_survey, responses)['comments']
    assert table.rows == []
    assert table.base == 1
