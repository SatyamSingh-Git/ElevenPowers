"""Cross-tabulations: one question's answers broken down by another's.

Cells hold column percentages: of the respondents in a column, the share who
gave each row answer. Only respondents who answered both questions count.
"""
from dataclasses import dataclass

from ..model.errors import SurveyError
from .weighting import weight_for


@dataclass
class Crosstab:
    row_question: object
    column_question: object
    rows: list
    columns: list
    cells: dict
    counts: dict
    column_bases: dict
    column_counts: dict
    row_totals: dict
    base: float

    def percent(self, row, column):
        base = self.column_bases[column]
        return 100 * self.cells[(row, column)] / base if base else 0.0

    def total_percent(self, row):
        return 100 * self.row_totals[row] / self.base if self.base else 0.0


def crosstab(survey, responses, row_id, column_id, weights=None):
    if row_id == column_id:
        raise SurveyError(f'{row_id} cannot be crossed with itself')
    row_question, column_question = survey.question(row_id), survey.question(column_id)
    rows, columns = row_question.categories(), column_question.categories()
    cells = {(row, column): 0.0 for row in rows for column in columns}
    counts = dict.fromkeys(cells, 0)
    column_bases = dict.fromkeys(columns, 0.0)
    column_counts = dict.fromkeys(columns, 0)
    row_totals = dict.fromkeys(rows, 0.0)
    base = 0.0
    for response in responses:
        row_values, column_values = response.chosen(row_id), response.chosen(column_id)
        if not row_values or not column_values:
            continue
        weight = weight_for(weights, response.respondent)
        base += weight
        for row in row_values:
            row_totals[row] += weight
        for column in column_values:
            column_bases[column] += weight
            column_counts[column] += 1
            for row in row_values:
                cells[(row, column)] += weight
                counts[(row, column)] += 1
    return Crosstab(row_question, column_question, rows, columns, cells, counts,
                    column_bases, column_counts, row_totals, base)
