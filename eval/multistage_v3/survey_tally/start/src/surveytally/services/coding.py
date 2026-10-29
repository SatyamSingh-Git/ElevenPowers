"""Coding free-text answers with a codeframe: keywords that put answers into codes.

A codeframe file is a CSV with the columns `code`, `label` and `keyword`, one
keyword per row; a code with several keywords takes several rows. An answer
gets every code with a keyword that appears in it as a whole word, ignoring
case. Answers that match no keyword are counted as uncoded.
"""
import csv
from dataclasses import dataclass
from pathlib import Path
import re

from ..model.errors import SurveyError
from ..model.questions import FreeText
from .weighting import weight_for

CODEFRAME_COLUMNS = ('code', 'label', 'keyword')
UNCODED_LABEL = '(uncoded)'


@dataclass
class Code:
    code: str
    label: str
    keywords: list

    def matches(self, text):
        return any(re.search(rf'\b{re.escape(keyword)}\b', text, re.IGNORECASE) for keyword in self.keywords)


@dataclass
class CodedRow:
    code: str
    label: str
    count: int
    percent: float


def read_codeframe(path):
    path = Path(path)
    codes = {}
    with path.open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in CODEFRAME_COLUMNS if column not in (reader.fieldnames or ())]
        if missing:
            raise SurveyError(f'{path.name}: missing column {missing[0]}')
        for number, row in enumerate(reader, start=2):
            code, keyword = row['code'].strip(), row['keyword'].strip()
            if not code or not keyword:
                raise SurveyError(f'{path.name} row {number}: code and keyword are both needed')
            entry = codes.setdefault(code, Code(code, row['label'].strip() or code, []))
            entry.keywords.append(keyword)
    return list(codes.values())


def code_answer(text, codeframe):
    return [code.code for code in codeframe if code.matches(text)]


def code_answers(survey, responses, question_id, codeframe, weights=None):
    """Rows for every code, then one for uncoded answers; percentages are of the weighted answers."""
    question = survey.question(question_id)
    if not isinstance(question, FreeText):
        raise SurveyError(f'{question_id} is not a free-text question')
    counts = {code.code: 0 for code in codeframe}
    weighted = {code.code: 0.0 for code in codeframe}
    uncoded, uncoded_weighted, base = 0, 0.0, 0.0
    for response in responses:
        text = response.answer(question_id)
        if text is None:
            continue
        weight = weight_for(weights, response.respondent)
        base += weight
        found = code_answer(text, codeframe)
        if not found:
            uncoded += 1
            uncoded_weighted += weight
        for code in found:
            counts[code] += 1
            weighted[code] += weight

    def percent(value):
        return 100 * value / base if base else 0.0

    rows = [CodedRow(code.code, code.label, counts[code.code], percent(weighted[code.code])) for code in codeframe]
    rows.append(CodedRow('', UNCODED_LABEL, uncoded, percent(uncoded_weighted)))
    return rows
