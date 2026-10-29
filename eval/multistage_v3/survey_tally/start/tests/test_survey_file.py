import json

import pytest

from surveytally.files.survey_file import load_survey, save_survey, survey_from_dict
from surveytally.model.errors import SurveyFileError

from conftest import CUSTOMER


def test_presets_fill_in_points_and_labels(customer_survey):
    question = customer_survey.question('satisfaction')
    assert (question.low, question.high) == (1, 5)
    assert question.label_for(5) == 'Strongly agree'


def test_plain_option_codes_are_their_own_labels(customer_survey):
    assert customer_survey.question('channels').label_for('web') == 'web'


def test_save_and_load_give_the_same_survey(tmp_path, customer_survey):
    path = tmp_path / 'survey.json'
    save_survey(customer_survey, path)
    loaded = load_survey(path)
    assert loaded.question_ids() == customer_survey.question_ids()
    assert loaded.question('recommend').labels == customer_survey.question('recommend').labels
    assert [score.name for score in loaded.scores] == ['overall', 'happy', 'nps']


def test_unknown_question_type_is_reported_with_the_file_name(write_file):
    data = {'id': 's', 'title': 'S', 'questions': [{'id': 'q1', 'type': 'ranking'}]}
    path = write_file('broken.json', json.dumps(data))
    with pytest.raises(SurveyFileError, match='broken.json: question q1 has unknown type ranking'):
        load_survey(path)


def test_newer_schema_is_refused():
    with pytest.raises(SurveyFileError, match='schema 9 is newer'):
        survey_from_dict({**CUSTOMER, 'schema': 9})


def test_invalid_json_names_the_line(write_file):
    path = write_file('bad.json', '{\n  "id": "s",\n  oops\n}')
    with pytest.raises(SurveyFileError, match='line 3'):
        load_survey(path)
