import json

from surveytally.files.csv_responses import read_responses
from surveytally.files.json_responses import read_json_responses
from surveytally.model.responses import Response
from surveytally.reports.responses_export import write_json_responses, write_responses


def test_csv_holds_one_column_per_question(tmp_path, customer_survey):
    path = tmp_path / 'out.csv'
    write_responses(customer_survey, [Response('R1', {'contact': 'email', 'ease': 4}, '2026-03-02', 90)], path)
    lines = path.read_text(encoding='utf-8').splitlines()
    assert lines[0] == 'respondent,submitted,duration,contact,channels,satisfaction,ease,recommend,comments'
    assert lines[1] == 'R1,2026-03-02,90,email,,,4,,'


def test_csv_can_be_imported_again(tmp_path, customer_survey):
    responses = [Response('R1', {'contact': 'post', 'satisfaction': 2, 'comments': 'Slow, but fine'}),
                 Response('R2', {'channels': ('store',)}, '2026-03-05')]
    path = tmp_path / 'out.csv'
    write_responses(customer_survey, responses, path)
    assert read_responses(customer_survey, path) == responses


def test_labels_replace_codes(tmp_path, customer_survey):
    path = tmp_path / 'out.csv'
    write_responses(customer_survey, [Response('R1', {'contact': 'email', 'satisfaction': 5})], path, labels=True)
    assert path.read_text(encoding='utf-8').splitlines()[1] == 'R1,,,Email,,Strongly agree,,,'


def test_json_lines_round_trip(tmp_path, customer_survey):
    responses = [Response('R1', {'channels': ('web', 'app'), 'recommend': 7}, '2026-03-02', 120)]
    path = tmp_path / 'out.jsonl'
    write_json_responses(customer_survey, responses, path)
    assert json.loads(path.read_text(encoding='utf-8'))['answers'] == {'channels': ['web', 'app'], 'recommend': 7}
    assert read_json_responses(customer_survey, path) == responses
