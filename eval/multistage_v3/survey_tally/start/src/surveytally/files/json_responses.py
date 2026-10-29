"""Response files in JSON lines: one JSON object per line, as web form tools export them.

    {"respondent": "R17", "submitted": "2026-03-02", "answers": {"contact": "email", "channels": ["web", "phone"]}}

Answers keep their JSON types: a list of option codes for multiple choice, a
whole number for a scale and a string otherwise. A null answer is no answer.
Errors name the line they were found on.
"""
import json
from datetime import date
from pathlib import Path

from ..model.errors import ResponseFileError
from ..model.questions import MultipleChoice, Scale
from ..model.responses import Response

RECORD_KEYS = ('respondent', 'submitted', 'duration', 'answers')


def read_json_responses(survey, path):
    responses = []
    with Path(path).open(encoding='utf-8-sig') as handle:
        for number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ResponseFileError(number, f'not valid JSON ({error.msg})') from None
            responses.append(_record(survey, record, number))
    return responses


def _record(survey, record, number):
    if not isinstance(record, dict):
        raise ResponseFileError(number, 'expected a JSON object')
    for key in record:
        if key not in RECORD_KEYS:
            raise ResponseFileError(number, f'unknown key {key}')
    respondent = str(record.get('respondent') or '').strip()
    if not respondent:
        raise ResponseFileError(number, 'no respondent id')
    raw = record.get('answers') or {}
    if not isinstance(raw, dict):
        raise ResponseFileError(number, 'answers must be an object keyed by question id')
    answers = {}
    for question_id, value in raw.items():
        if not survey.has_question(question_id):
            raise ResponseFileError(number, f'unknown question {question_id}')
        if value is not None:
            answers[question_id] = _answer(survey.question(question_id), value, number)
    return Response(respondent, answers, _submitted(record, number), _duration(record, number))


def _answer(question, value, number):
    if isinstance(question, MultipleChoice):
        if not isinstance(value, list) or not all(isinstance(code, str) for code in value):
            raise ResponseFileError(number, f'{question.id} expects a list of option codes')
        return tuple(value)
    if isinstance(question, Scale):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ResponseFileError(number, f'{question.id} expects a whole number, got {value!r}')
        return value
    if not isinstance(value, str):
        raise ResponseFileError(number, f'{question.id} expects a string, got {value!r}')
    return value


def _submitted(record, number):
    value = record.get('submitted') or ''
    if not value:
        return ''
    try:
        return date.fromisoformat(value).isoformat()
    except (TypeError, ValueError):
        raise ResponseFileError(number, f'submitted must be a date like 2026-03-31, got {value}') from None


def _duration(record, number):
    value = record.get('duration')
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ResponseFileError(number, f'duration must be whole seconds, got {value!r}')
    return value
