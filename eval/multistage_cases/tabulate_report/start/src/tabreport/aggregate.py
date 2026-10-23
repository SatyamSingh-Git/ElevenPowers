"""Grouping rows and computing measures over each group."""
from dataclasses import dataclass
from decimal import Decimal

from .errors import ReportError
from .numbers import parse_amount

FUNCTIONS = ("sum", "count", "mean", "min", "max")
KEY_SEPARATOR = " / "


@dataclass(frozen=True)
class Measure:
    func: str
    column: str | None = None

    @property
    def label(self):
        return self.func if self.column is None else f"{self.func}({self.column})"


def parse_measure(spec):
    """``sum:amount`` is Measure("sum", "amount"); a bare ``count`` counts rows."""
    if isinstance(spec, Measure):
        return spec
    func, _, column = spec.partition(":")
    func, column = func.strip().lower(), column.strip()
    if func not in FUNCTIONS:
        raise ReportError(f"unknown measure: {func}")
    if func == "count":
        if column:
            raise ReportError("count takes no column")
        return Measure("count")
    if not column:
        raise ReportError(f"measure needs a column: {func}")
    return Measure(func, column)


class _Stats:
    __slots__ = ("count", "total", "low", "high")

    def __init__(self):
        self.count, self.total, self.low, self.high = 0, Decimal(0), None, None

    def add(self, value):
        self.count += 1
        self.total += value
        if self.low is None or value < self.low:
            self.low = value
        if self.high is None or value > self.high:
            self.high = value


class Accumulator:
    """Running results for one group, fed a row at a time. Blank cells are skipped."""

    def __init__(self, measures):
        self.measures = measures
        self.rows = 0
        self.stats = {m.column: _Stats() for m in measures if m.column is not None}

    def add(self, row):
        self.rows += 1
        for column, stats in self.stats.items():
            text = cell(row, column)
            if text.strip():
                stats.add(parse_amount(text))

    def result(self, measure):
        if measure.func == "count":
            return self.rows
        stats = self.stats[measure.column]
        if measure.func == "sum":
            return stats.total
        if measure.func == "mean":
            return stats.total / stats.count if stats.count else None
        return stats.low if measure.func == "min" else stats.high

    def results(self):
        return {m.label: self.result(m) for m in self.measures}


def aggregate(rows, by, measures):
    """One dict per distinct key of the ``by`` columns, in the order keys first appear.

    The key is under ``"group"``, multi-column keys joined with KEY_SEPARATOR;
    each measure is under its label.
    """
    measures = [parse_measure(m) for m in measures]
    groups = {}
    for row in rows:
        key = tuple(cell(row, name) for name in by)
        if key not in groups:
            groups[key] = Accumulator(measures)
        groups[key].add(row)
    return [{"group": KEY_SEPARATOR.join(key), **totals.results()} for key, totals in groups.items()]


def cell(row, name):
    try:
        return row[name]
    except KeyError:
        raise ReportError(f"missing column: {name}") from None
