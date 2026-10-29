"""Stage 6: respondent ids read from response files are kept in upper case."""
import json

from surveytally.files.csv_responses import read_responses
from surveytally.files.json_responses import read_json_responses
from surveytally.files.survey_file import load_survey

SURVEY = {
    'id': 'panel',
    'title': 'Panel wave',
    'questions': [{'id': 'shop', 'type': 'single', 'text': 'Where do you shop?', 'options': ['online', 'store']}],
}


def survey(tmp_path):
    path = tmp_path / 'panel.json'
    path.write_text(json.dumps(SURVEY), encoding='utf-8')
    return load_survey(path)


def test_csv_ids_in_upper_case(tmp_path):
    path = tmp_path / 'responses.csv'
    path.write_text('respondent,shop\nab12,online\nCd34x,store\nEF56,online\n', encoding='utf-8')
    assert [response.respondent for response in read_responses(survey(tmp_path), path)] == ['AB12', 'CD34X', 'EF56']


def test_json_lines_ids_in_upper_case(tmp_path):
    path = tmp_path / 'responses.jsonl'
    path.write_text('{"respondent": "gh78", "answers": {"shop": "store"}}\n', encoding='utf-8')
    assert [response.respondent for response in read_json_responses(survey(tmp_path), path)] == ['GH78']
