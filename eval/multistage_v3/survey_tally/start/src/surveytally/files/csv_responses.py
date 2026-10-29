"""Response CSV files: one row per response, one column per question.

The `respondent` column is required; `submitted` and `duration` are optional.
Every other column must be the id of a question in the survey. Cells are read
according to the question's type; checking them against the questionnaire is
left to validation.
"""
import csv
from datetime import date
from pathlib import Path

from ..model.errors import ResponseFileError
from ..model.responses import Response

RESPONDENT_COLUMN = 'respondent'
SUBMITTED_COLUMN = 'submitted'
DURATION_COLUMN = 'duration'
FIXED_COLUMNS = (RESPONDENT_COLUMN, SUBMITTED_COLUMN, DURATION_COLUMN)
MISSING = ('', 'NA')
MULTI_SEPARATOR = ';'


def read_responses(survey, path):
    path = Path(path)
    with path.open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ResponseFileError(1, 'the file is empty')
        _check_header(survey, reader.fieldnames)
        return [_response(survey, row, number) for number, row in enumerate(reader, start=2)]


def _check_header(survey, columns):
    if RESPONDENT_COLUMN not in columns:
        raise ResponseFileError(1, f'missing column {RESPONDENT_COLUMN}')
    seen = set()
    for column in columns:
        if column in seen:
            raise ResponseFileError(1, f'column {column} appears twice')
        seen.add(column)
        if column not in FIXED_COLUMNS and not survey.has_question(column):
            raise ResponseFileError(1, f'unknown question column {column}')


def _response(survey, row, number):
    if None in row:
        raise ResponseFileError(number, 'more cells than columns')
    respondent = row[RESPONDENT_COLUMN].strip()
    if not respondent:
        raise ResponseFileError(number, 'no respondent id')
    answers = {}
    for question in survey.questions:
        cell = (row.get(question.id) or '').strip()
        if cell in MISSING:
            continue
        answers[question.id] = PARSERS[question.type](question, cell, number)
    return Response(respondent, answers, _submitted(row, number), _duration(row, number))


def _submitted(row, number):
    value = (row.get(SUBMITTED_COLUMN) or '').strip()
    if not value:
        return ''
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        raise ResponseFileError(number, f'submitted must be a date like 2026-03-31, got {value}') from None


def _duration(row, number):
    value = (row.get(DURATION_COLUMN) or '').strip()
    if value in MISSING:
        return None
    if not value.isdigit():
        raise ResponseFileError(number, f'duration must be whole seconds, got {value}')
    return int(value)


def _parse_code(question, cell, number):
    return cell


def _parse_codes(question, cell, number):
    return tuple(code.strip() for code in cell.split(MULTI_SEPARATOR) if code.strip())


def _parse_point(question, cell, number):
    try:
        return int(cell)
    except ValueError:
        raise ResponseFileError(number, f'{question.id} expects a whole number, got {cell}') from None


def _parse_text(question, cell, number):
    return cell


PARSERS = {
    'single': _parse_code,
    'multi': _parse_codes,
    'scale': _parse_point,
    'text': _parse_text,
}
