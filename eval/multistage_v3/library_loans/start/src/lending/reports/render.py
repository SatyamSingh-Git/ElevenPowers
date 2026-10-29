"""Turning report rows (dicts sharing the same keys) into text, CSV or JSON."""
import csv
import io
import json


def _text(rows, columns):
    if not rows:
        return '(nothing to report)\n'
    cells = [[str(row[column]) for column in columns] for row in rows]
    widths = [max(len(column), *(len(line[i]) for line in cells)) for i, column in enumerate(columns)]
    lines = ['  '.join(column.ljust(width) for column, width in zip(columns, widths)).rstrip()]
    lines.append('  '.join('-' * width for width in widths))
    lines += ['  '.join(cell.ljust(width) for cell, width in zip(line, widths)).rstrip() for line in cells]
    return '\n'.join(lines) + '\n'


def _csv(rows, columns):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=columns, lineterminator='\n', extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def _json(rows, columns):
    return json.dumps([{column: row[column] for column in columns} for row in rows], indent=2) + '\n'


FORMATS = {'text': _text, 'csv': _csv, 'json': _json}


def render(rows, columns, fmt='text'):
    return FORMATS[fmt](rows, columns)
