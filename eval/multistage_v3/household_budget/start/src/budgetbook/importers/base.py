"""Reading a bank's CSV statement into rows the ledger understands."""
import csv
from dataclasses import dataclass
import datetime as dt
import io
from typing import Callable

from ..errors import BudgetError, StatementError
from ..model.dates import parse_date


@dataclass(frozen=True)
class StatementRow:
    line: int
    date: dt.date
    payee: str
    amount: int
    memo: str = ""


@dataclass(frozen=True)
class Problem:
    """A statement row that was left out, and why."""

    line: int
    message: str

    def __str__(self):
        return f"line {self.line}: {self.message}"


@dataclass(frozen=True)
class Layout:
    """How one bank's export maps onto statement rows.

    `amount` turns a row's values, keyed by column name, into cents with money
    out negative; each layout knows how its bank writes amounts.
    """

    name: str
    columns: tuple
    date_column: str
    date_style: str
    payee_column: str
    amount: Callable[[dict], int]
    memo_column: str = ""

    def read(self, text):
        """The statement's rows, and a problem for each row that could not be read."""
        reader = csv.DictReader(io.StringIO(_without_bom(text)))
        header = [name.strip() for name in reader.fieldnames or []]
        for column in self.columns:
            if column not in header:
                raise StatementError(f"{self.name} statement is missing column: {column}")
        reader.fieldnames = header
        rows, problems = [], []
        for record in reader:
            values = {key: (value or "").strip() for key, value in record.items() if key is not None}
            if not any(values.values()):
                continue
            try:
                rows.append(self._row(reader.line_num, values))
            except BudgetError as error:
                problems.append(Problem(reader.line_num, str(error)))
        return rows, problems

    def _row(self, line, values):
        payee = values[self.payee_column]
        if not payee:
            raise StatementError("payee is empty")
        day = parse_date(values[self.date_column], self.date_style)
        memo = values.get(self.memo_column, "") if self.memo_column else ""
        return StatementRow(line, day, payee, self.amount(values), memo)


def header_of(text):
    """The column names in a statement's first row."""
    first = next(csv.reader(io.StringIO(_without_bom(text))), [])
    return [name.strip() for name in first]


def _without_bom(text):
    return text[1:] if text.startswith("﻿") else text
