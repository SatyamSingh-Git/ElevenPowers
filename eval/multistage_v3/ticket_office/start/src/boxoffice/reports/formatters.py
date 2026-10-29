"""Turns a report's columns and rows into a text table, CSV or JSON.

A report is a list of `Column`s and a list of row dicts keyed by column name.
Money is whole pence in the rows: text and CSV show it as pounds and pence,
JSON keeps the pence so that other programs can add it up.
"""
import csv
from dataclasses import dataclass
import io
import json

from ..model.money import format_pence

FORMATS = ("text", "csv", "json", "markdown")
NUMERIC = ("int", "money", "percent")


@dataclass(frozen=True)
class Column:
    name: str
    kind: str = "text"


def render(columns, rows, fmt="text"):
    if fmt == "json":
        return json.dumps([{column.name: row[column.name] for column in columns} for row in rows], indent=2)
    cells = [[_cell(column, row[column.name]) for column in columns] for row in rows]
    if fmt == "csv":
        return _csv(columns, cells)
    if fmt == "text":
        return _table(columns, cells)
    if fmt == "markdown":
        return _markdown(columns, cells)
    raise ValueError(f"unknown format {fmt}; choose from {', '.join(FORMATS)}")


def _cell(column, value):
    if column.kind == "money":
        return format_pence(value)
    if column.kind == "percent":
        return f"{value:.1f}%"
    return str(value)


def _csv(columns, cells):
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow([column.name for column in columns])
    writer.writerows(cells)
    return buffer.getvalue().rstrip("\n")


def _markdown(columns, cells):
    """A pipe table for pasting into the team wiki; numbers are right-aligned."""
    header = "| " + " | ".join(column.name for column in columns) + " |"
    rule = "|" + "|".join("---:" if column.kind in NUMERIC else "---" for column in columns) + "|"
    body = ["| " + " | ".join(value.replace("|", "/") for value in row) + " |" for row in cells]
    return "\n".join([header, rule, *body])


def _table(columns, cells):
    widths = [max([len(column.name), *(len(row[i]) for row in cells)]) for i, column in enumerate(columns)]

    def line(values):
        parts = [value.rjust(width) if column.kind in NUMERIC else value.ljust(width)
                 for column, value, width in zip(columns, values, widths)]
        return "  ".join(parts).rstrip()

    header = line([column.name for column in columns])
    rule = "  ".join("-" * width for width in widths)
    return "\n".join([header, rule, *(line(row) for row in cells)])
