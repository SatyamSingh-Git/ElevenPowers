"""Banner tables: one question's answers down the side, several questions across the top.

A banner puts the crosstabs of one row question side by side, after a Total
column, so subgroups can be read along a single line.
"""
from ..services.crosstab import crosstab
from ..services.significance import significance
from .formatting import format_number, format_percent
from .tables import BASE_LABEL, TOTAL_LABEL, Table


def banner_table(survey, responses, row_id, column_ids, weights=None, decimals=1, letters=False):
    if not column_ids:
        raise ValueError('a banner needs at least one column question')
    tabs = [crosstab(survey, responses, row_id, column_id, weights) for column_id in column_ids]
    row_question = survey.question(row_id)
    columns = [row_question.id, TOTAL_LABEL]
    for tab in tabs:
        columns += [f'{tab.column_question.id}: {tab.column_question.label_for(column)}' for column in tab.columns]
    marks = [significance(tab) if letters else {} for tab in tabs]
    first = tabs[0]
    rows = []
    for row in row_question.categories():
        cells = [row_question.label_for(row), format_percent(first.total_percent(row), decimals)]
        for tab, found in zip(tabs, marks):
            for column in tab.columns:
                cell = format_percent(tab.percent(row, column), decimals)
                if found.get((row, column)):
                    cell += f' {found[(row, column)]}'
                cells.append(cell)
        rows.append(cells)
    bases = [BASE_LABEL, format_number(first.base, 1)]
    for tab in tabs:
        bases += [format_number(tab.column_bases[column], 1) for column in tab.columns]
    rows.append(bases)
    notes = ['Column percentages; Total is of respondents who answered the first banner question']
    if letters:
        notes.append('Letters mark a percentage significantly above that column within the same question')
    return Table(f'{row_id} by {", ".join(column_ids)}', columns, rows, notes)
