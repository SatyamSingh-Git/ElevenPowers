import pytest

from surveytally.files.csv_responses import read_responses
from surveytally.model.errors import ResponseFileError


def test_reads_answers_by_question_type(customer_survey, write_file):
    path = write_file('responses.csv', (
        'respondent,submitted,duration,contact,channels,satisfaction,comments\n'
        'R1,2026-03-02,340,email,web,4,Quick and friendly\n'
    ))
    [response] = read_responses(customer_survey, path)
    assert response.respondent == 'R1'
    assert response.submitted == '2026-03-02'
    assert response.duration == 340
    assert response.answers == {'contact': 'email', 'channels': ('web',), 'satisfaction': 4,
                                'comments': 'Quick and friendly'}


def test_empty_and_na_cells_are_unanswered(customer_survey, write_file):
    path = write_file('responses.csv', 'respondent,contact,ease,comments\nR1,NA,,\n')
    [response] = read_responses(customer_survey, path)
    assert response.answers == {}


def test_columns_must_be_questions(customer_survey, write_file):
    path = write_file('responses.csv', 'respondent,colour\nR1,blue\n')
    with pytest.raises(ResponseFileError, match='row 1: unknown question column colour'):
        read_responses(customer_survey, path)


def test_scale_cells_must_be_whole_numbers(customer_survey, write_file):
    path = write_file('responses.csv', 'respondent,ease\nR1,4\nR2,four\n')
    with pytest.raises(ResponseFileError, match='row 3: ease expects a whole number, got four'):
        read_responses(customer_survey, path)


def test_submitted_must_be_a_date(customer_survey, write_file):
    path = write_file('responses.csv', 'respondent,submitted\nR1,02/03/2026\n')
    with pytest.raises(ResponseFileError, match='submitted must be a date'):
        read_responses(customer_survey, path)


def test_respondent_column_is_required(customer_survey, write_file):
    path = write_file('responses.csv', 'contact\nemail\n')
    with pytest.raises(ResponseFileError, match='missing column respondent'):
        read_responses(customer_survey, path)
