"""Stage 7: text questions without their own max_length accept answers up to 2000 characters."""
import json

from surveytally.files.survey_file import load_survey
from surveytally.model.responses import Response
from surveytally.services.validation import validate

SURVEY = {
    'id': 'feedback',
    'title': 'Open feedback',
    'questions': [
        {'id': 'story', 'type': 'text', 'text': 'Tell us what happened'},
        {'id': 'short', 'type': 'text', 'text': 'One word', 'max_length': 30},
    ],
}


def survey(tmp_path):
    path = tmp_path / 'feedback.json'
    path.write_text(json.dumps(SURVEY), encoding='utf-8')
    return load_survey(path)


def messages(tmp_path, answers):
    _, issues = validate(survey(tmp_path), [Response('F1', answers)])
    return [issue.message for issue in issues]


def test_answers_up_to_2000_characters_pass(tmp_path):
    assert messages(tmp_path, {'story': 'a' * 1200}) == []
    assert messages(tmp_path, {'story': 'a' * 2000}) == []


def test_longer_answers_name_the_new_limit(tmp_path):
    assert messages(tmp_path, {'story': 'a' * 2001}) == ['story: answer longer than 2000 characters']
    assert messages(tmp_path, {'short': 'a' * 31}) == ['short: answer longer than 30 characters']
