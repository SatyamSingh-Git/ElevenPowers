"""A codebook: every question with its type, text and the codes its answers use.

Analysts receiving a response CSV file read it next to the codebook.
"""
import csv
from pathlib import Path

from ..model.questions import ChoiceQuestion, FreeText, MultipleChoice, Scale
from .render import RENDERERS
from .tables import Table

CODEBOOK_COLUMNS = ('question', 'type', 'code', 'label')


def codebook_rows(survey):
    """One row per answer code; a free-text question gets one row describing its limit."""
    rows = []
    for question in survey.questions:
        rows.append([question.id, question.type, '', question.text])
        rows.extend([question.id, question.type, str(code), label] for code, label in _codes(question))
    return rows


def _codes(question):
    if isinstance(question, ChoiceQuestion):
        codes = [(option.code, option.label) for option in question.options]
        if isinstance(question, MultipleChoice) and question.max_choices is not None:
            codes.append(('', f'(choose up to {question.max_choices})'))
        return codes
    if isinstance(question, Scale):
        return [(point, question.label_for(point)) for point in question.points()]
    if isinstance(question, FreeText):
        return [('', f'(free text, up to {question.max_length} characters)')]
    return []


def write_codebook(survey, path, format='csv'):
    rows = codebook_rows(survey)
    if format == 'csv':
        with Path(path).open('w', newline='', encoding='utf-8') as handle:
            writer = csv.writer(handle)
            writer.writerow(CODEBOOK_COLUMNS)
            writer.writerows(rows)
        return
    table = Table(f'Codebook: {survey.title}', [column.title() for column in CODEBOOK_COLUMNS], rows)
    Path(path).write_text(RENDERERS[format](table) + '\n', encoding='utf-8')
