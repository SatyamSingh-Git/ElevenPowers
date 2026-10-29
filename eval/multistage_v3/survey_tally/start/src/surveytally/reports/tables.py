"""Tables ready to render: a title, column headings, rows of text and notes."""
from dataclasses import dataclass, field

from .formatting import MEAN_DECIMALS, format_number, format_percent, format_score

MISSING_LABEL = '(no answer)'
TOTAL_LABEL = 'Total'
BASE_LABEL = 'n'


@dataclass
class Table:
    title: str
    columns: list
    rows: list
    notes: list = field(default_factory=list)


def frequency_table(table, decimals=1):
    title = f'{table.question_id}. {table.text}' if table.text else table.question_id
    rows = [[row.label, str(row.count), format_percent(row.percent, decimals)] for row in table.rows]
    if table.missing:
        rows.append([MISSING_LABEL, str(table.missing), ''])
    notes = [f'Base: {table.base} answered']
    if table.mean is not None:
        notes.append(f'Mean: {format_number(table.mean, MEAN_DECIMALS)}')
    return Table(title, ['Answer', 'Count', '%'], rows, notes)


def crosstab_table(crosstab, decimals=1, labels=True, marks=None):
    """Column percentages, a Total column and a final row of column bases.

    With `labels` false, rows and columns are named by code, as machine-readable
    exports want. `marks` are significance letters by (row, column), shown after
    the percentage.
    """
    row_question, column_question = crosstab.row_question, crosstab.column_question
    marks = marks or {}

    def name(question, value):
        return question.label_for(value) if labels else str(value)

    def cell(row, column):
        text = format_percent(crosstab.percent(row, column), decimals)
        return f'{text} {marks[(row, column)]}' if marks.get((row, column)) else text

    columns = [row_question.id] + [name(column_question, column) for column in crosstab.columns] + [TOTAL_LABEL]
    rows = []
    for row in crosstab.rows:
        cells = [cell(row, column) for column in crosstab.columns]
        rows.append([name(row_question, row), *cells, format_percent(crosstab.total_percent(row), decimals)])
    bases = [format_number(crosstab.column_bases[column], 1) for column in crosstab.columns]
    rows.append([BASE_LABEL, *bases, format_number(crosstab.base, 1)])
    title = f'{row_question.id} by {column_question.id}'
    return Table(title, columns, rows, ['Column percentages of respondents who answered both questions'])


def scores_table(scores, decimals=1):
    rows = [[result.title, result.rule, format_score(result.mean, result.rule, decimals), str(result.base)]
            for result in scores.values()]
    return Table('Scores', ['Score', 'Rule', 'Value', 'Base'], rows)
