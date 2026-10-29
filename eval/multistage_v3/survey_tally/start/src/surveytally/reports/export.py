"""Exporting result tables to files: CSV for other tools, Markdown or text for people.

The CSV export of frequency tables is long-format: one row per answer option,
named by its code, followed by a row for the respondents who gave no answer.
"""
import csv
from pathlib import Path

from .formatting import format_percent
from .render import RENDERERS
from .tables import MISSING_LABEL, crosstab_table, frequency_table, scores_table

FREQUENCY_COLUMNS = ('question', 'option', 'count', 'percent')
EXPORT_FORMATS = ('csv', 'markdown', 'text')


def export_frequencies(tables, path, format='csv', decimals=1):
    _check_format(format)
    if format == 'csv':
        _write_csv(path, FREQUENCY_COLUMNS, frequency_rows(tables, decimals))
    else:
        _write_rendered(path, [frequency_table(table, decimals) for table in tables.values() if table.rows], format)


def frequency_rows(tables, decimals=1):
    """CSV rows for every question that has answer options; free-text questions have none."""
    rows = []
    for table in tables.values():
        if not table.rows:
            continue
        for row in table.rows:
            rows.append([table.question_id, row.code, row.count, format_percent(row.percent, decimals)])
        if table.missing:
            rows.append([table.question_id, MISSING_LABEL, table.missing, ''])
    return rows


def export_crosstab(crosstab, path, format='csv', decimals=1):
    _check_format(format)
    if format == 'csv':
        table = crosstab_table(crosstab, decimals, labels=False)
        _write_csv(path, table.columns, table.rows)
    else:
        _write_rendered(path, [crosstab_table(crosstab, decimals)], format)


def export_scores(scores, path, format='csv', decimals=1):
    _check_format(format)
    table = scores_table(scores, decimals)
    if format == 'csv':
        _write_csv(path, [column.lower() for column in table.columns], table.rows)
    else:
        _write_rendered(path, [table], format)


def _check_format(format):
    if format not in EXPORT_FORMATS:
        raise ValueError(f'unknown export format {format}; choose one of {", ".join(EXPORT_FORMATS)}')


def _write_csv(path, columns, rows):
    with Path(path).open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)


def _write_rendered(path, tables, format):
    render = RENDERERS[format]
    Path(path).write_text('\n\n'.join(render(table) for table in tables) + '\n', encoding='utf-8')
