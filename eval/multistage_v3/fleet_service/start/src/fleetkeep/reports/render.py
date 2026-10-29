"""Printing report rows as a text table, CSV or JSON."""
import csv
from datetime import date
from decimal import Decimal
import io
import json

from .layout import LAYOUTS


def _text(value):
    if value is None:
        return ""
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _json(value):
    if isinstance(value, (Decimal, date)):
        return _text(value)
    return value


def render_table(columns, rows):
    cells = [[column.name for column in columns]]
    cells += [[_text(value) or "-" for value in row] for row in rows]
    widths = [max(len(line[i]) for line in cells) for i in range(len(columns))]

    def line(values):
        padded = (value.rjust(width) if column.align == "right" else value.ljust(width)
                  for value, width, column in zip(values, widths, columns, strict=True))
        return "  ".join(padded).rstrip()

    out = [line(cells[0]), "  ".join("-" * width for width in widths)]
    out += [line(values) for values in cells[1:]]
    return "\n".join(out) + "\n"


def render_csv(columns, rows):
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(column.name for column in columns)
    for row in rows:
        writer.writerow(_text(value) for value in row)
    return buffer.getvalue()


def render_json(columns, rows):
    names = [column.name for column in columns]
    records = [{name: _json(value) for name, value in zip(names, row, strict=True)}
               for row in rows]
    return json.dumps(records, indent=2) + "\n"


RENDERERS = {
    "table": render_table,
    "csv": render_csv,
    "json": render_json,
}


def render(report, rows, fmt):
    return RENDERERS[fmt](LAYOUTS[report], rows)
