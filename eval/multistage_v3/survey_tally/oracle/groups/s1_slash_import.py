"""Stage 1: multiple-choice cells in response CSV files are separated by `/`."""
import json

from surveytally.files.csv_responses import read_responses
from surveytally.files.survey_file import load_survey
from surveytally.services.validation import validate

SURVEY = {
    'id': 'event',
    'title': 'Event feedback',
    'questions': [
        {'id': 'sessions', 'type': 'multi', 'text': 'Which sessions did you attend?',
         'options': ['keynote', 'workshop', 'panel', 'social']},
        {'id': 'day', 'type': 'single', 'text': 'Which day?', 'options': ['mon', 'tue']},
    ],
}


def load(tmp_path):
    path = tmp_path / 'event.json'
    path.write_text(json.dumps(SURVEY), encoding='utf-8')
    return load_survey(path)


def test_slash_separates_the_chosen_options(tmp_path):
    survey = load(tmp_path)
    path = tmp_path / 'responses.csv'
    path.write_text('respondent,sessions,day\nA1,keynote/panel,mon\nA2,workshop/social/keynote,tue\nA3,panel,mon\n',
                    encoding='utf-8')
    responses = read_responses(survey, path)
    assert [response.answers['sessions'] for response in responses] == [
        ('keynote', 'panel'), ('workshop', 'social', 'keynote'), ('panel',)]
    valid, issues = validate(survey, responses)
    assert issues == []
    assert len(valid) == 3
