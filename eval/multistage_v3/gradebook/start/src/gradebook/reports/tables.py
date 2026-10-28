"""A report table: what every formatter renders."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Table:
    title: str
    columns: tuple
    rows: list  # lists of strings, one per column
    notes: list = field(default_factory=list)
    numeric: frozenset = frozenset()  # columns to right-align where the format allows

    def column(self, name):
        index = self.columns.index(name)
        return [row[index] for row in self.rows]
