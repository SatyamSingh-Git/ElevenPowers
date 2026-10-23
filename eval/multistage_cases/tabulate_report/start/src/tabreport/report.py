"""A grouped report: one row per key, a TOTAL row, rendered as a table."""
from dataclasses import dataclass

from .aggregate import Accumulator, aggregate, parse_measure
from .errors import ReportError
from .money import currency as check_currency, format_money
from .numbers import format_number
from .table import render_table

TOTAL_LABEL = "TOTAL"


@dataclass
class Report:
    headers: list
    rows: list
    totals: list | None
    measures: list
    currency: str | None
    row_count: int

    @property
    def key_columns(self):
        return len(self.headers) - len(self.measures)


def build_report(rows, by, measures, currency="USD", totals=True, sort=None):
    """Group ``rows``, a list of dicts as read_csv returns them, by the ``by`` columns.

    Every measure except count is money in ``currency``; None prints plain numbers.
    ``sort`` names a column to order by, descending when it starts with "-";
    groups are otherwise in key order.
    """
    measures = [parse_measure(m) for m in measures]
    if not measures:
        raise ReportError("at least one measure is needed")
    if currency is not None:
        check_currency(currency)
    keys = ["group"] if by else []
    headers = keys + [m.label for m in measures]
    results = aggregate(rows, by, measures) if by else []
    body = [([r["group"]] if by else []) + [r[m.label] for m in measures] for r in results]
    body.sort(key=lambda row: row[:len(keys)])
    if sort:
        body = _sorted(body, headers, sort)
    grand = None
    if totals:
        overall = Accumulator(measures)
        for row in rows:
            overall.add(row)
        label = [TOTAL_LABEL] if keys else []
        grand = label + [overall.result(m) for m in measures]
    return Report(headers, body, grand, measures, currency, len(rows))


def _sorted(body, headers, sort):
    descending = sort.startswith("-")
    name = sort.lstrip("-")
    if name not in headers:
        raise ReportError(f"unknown sort column: {name}")
    index = headers.index(name)
    present = [row for row in body if row[index] is not None]
    missing = [row for row in body if row[index] is None]
    return sorted(present, key=lambda row: row[index], reverse=descending) + missing


def render_report(report, fmt="plain"):
    rows = [_cells(report, row) for row in report.rows]
    totals = None if report.totals is None else _cells(report, report.totals)
    table = render_table(report.headers, rows, fmt, totals=totals)
    noun = "row" if report.row_count == 1 else "rows"
    return f"{table}\n{report.row_count} {noun}\n"


def _cells(report, row):
    keys = report.key_columns
    measured = zip(report.measures, row[keys:])
    return list(row[:keys]) + [_measure_cell(m, value, report.currency) for m, value in measured]


def _measure_cell(measure, value, currency):
    if value is None:
        return ""
    if measure.func == "count":
        return format_number(value, 0)
    if currency is None:
        return format_number(value)
    return format_money(value, currency)
