"""Writing responses back out, for clients or for another import: as a response
CSV file or as JSON lines.

With `labels`, the CSV holds the labels of choice and scale answers rather than
their codes, which reads better but cannot be imported again.
"""
import csv
import json
from pathlib import Path

CHOICE_SEPARATOR = ';'
LEADING_COLUMNS = ('respondent', 'submitted', 'duration')


def write_responses(survey, responses, path, labels=False):
    columns = [*LEADING_COLUMNS, *survey.question_ids()]
    with Path(path).open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        for response in responses:
            duration = '' if response.duration is None else str(response.duration)
            cells = [_cell(question, response.answer(question.id), labels) for question in survey.questions]
            writer.writerow([response.respondent, response.submitted, duration, *cells])


def _cell(question, value, labels):
    if value is None:
        return ''
    if isinstance(value, tuple):
        return CHOICE_SEPARATOR.join(question.label_for(code) if labels else code for code in value)
    return question.label_for(value) if labels else str(value)


def write_json_responses(survey, responses, path):
    """JSON lines, one response per line, with answers in questionnaire order."""
    with Path(path).open('w', encoding='utf-8') as handle:
        for response in responses:
            record = {'respondent': response.respondent}
            if response.submitted:
                record['submitted'] = response.submitted
            if response.duration is not None:
                record['duration'] = response.duration
            record['answers'] = {
                question.id: list(value) if isinstance(value, tuple) else value
                for question in survey.questions
                if (value := response.answer(question.id)) is not None
            }
            handle.write(json.dumps(record, ensure_ascii=False) + '\n')
