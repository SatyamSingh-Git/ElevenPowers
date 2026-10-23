"""Row filters as typed on the command line: ``region=East``, ``amount>=100``."""
from dataclasses import dataclass
import operator
import re

from .aggregate import cell
from .errors import ReportError
from .numbers import parse_amount

_FILTER = re.compile(r"\s*([^=!<>]+?)\s*(!=|>=|<=|=|>|<)\s*(.*?)\s*")
_COMPARE = {">": operator.gt, ">=": operator.ge, "<": operator.lt, "<=": operator.le}
OPERATORS = ("=", "!=", ">", ">=", "<", "<=")


@dataclass(frozen=True)
class Filter:
    column: str
    op: str
    value: str

    def matches(self, row):
        text = cell(row, self.column)
        if self.op == "=":
            return text == self.value
        if self.op == "!=":
            return text != self.value
        # A blank cell is neither above nor below anything.
        if not text.strip():
            return False
        return _COMPARE[self.op](parse_amount(text), parse_amount(self.value))


def parse_filter(text):
    match = _FILTER.fullmatch(text)
    if not match:
        raise ReportError(f"bad filter: {text!r}")
    column, op, value = match.groups()
    if op in _COMPARE:
        parse_amount(value)
    return Filter(column, op, value)


def keep(rows, filters):
    return [row for row in rows if all(f.matches(row) for f in filters)]
