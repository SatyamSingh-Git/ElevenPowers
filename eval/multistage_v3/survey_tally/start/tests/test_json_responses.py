import pytest

from surveytally.files.json_responses import read_json_responses
from surveytally.model.errors import ResponseFileError


def test_reads_json_lines(customer_survey, write_file):
    path = write_file('responses.jsonl', (
        '{"respondent": "R1", "submitted": "2026-03-02", "answers": {"contact": "post", "channels": ["app", "web"]}}\n'
        '\n'
        '{"respondent": "R2", "answers": {"recommend": 9, "comments": null}}\n'
    ))
    first, second = read_json_responses(customer_survey, path)
    assert first.answers == {'contact': 'post', 'channels': ('app', 'web')}
    assert second.answers == {'recommend': 9}
    assert second.submitted == ''


def test_scale_answers_must_be_numbers(customer_survey, write_file):
    path = write_file('responses.jsonl', '{"respondent": "R1", "answers": {"ease": "4"}}\n')
    with pytest.raises(ResponseFileError, match="row 1: ease expects a whole number, got '4'"):
        read_json_responses(customer_survey, path)


def test_unknown_questions_are_refused(customer_survey, write_file):
    path = write_file('responses.jsonl', '{"respondent": "R1", "answers": {"colour": "blue"}}\n')
    with pytest.raises(ResponseFileError, match='unknown question colour'):
        read_json_responses(customer_survey, path)
