"""Comparing two waves of a survey from their exported frequency tables (CSV).

Earlier waves are often only kept as the CSV export that was delivered, so the
comparison reads those files rather than project folders.
"""
import csv
from dataclasses import dataclass
from pathlib import Path

CHANGE_COLUMNS = ('question', 'option', 'before', 'after', 'change')


@dataclass(frozen=True)
class Change:
    question: str
    option: str
    before: float | None
    after: float | None

    @property
    def points(self):
        """The change in percentage points, or None when one wave lacks the option."""
        if self.before is None or self.after is None:
            return None
        return self.after - self.before


def read_percentages(path):
    """Percentages by (question, option code); rows without a percentage are skipped."""
    percentages = {}
    with Path(path).open(newline='', encoding='utf-8') as handle:
        rows = csv.reader(handle)
        next(rows, None)
        for question, option, _count, percent in rows:
            if percent:
                percentages[(question, option)] = float(percent)
    return percentages


def compare(before_path, after_path):
    """Changes for every option in either wave: the later wave's order first, then options it dropped."""
    before, after = read_percentages(before_path), read_percentages(after_path)
    keys = list(after) + [key for key in before if key not in after]
    return [Change(question, option, before.get((question, option)), after.get((question, option)))
            for question, option in keys]


def format_changes(changes, decimals=1, threshold=0.0):
    """A text table of the changes at least `threshold` points in size; new or dropped options always show."""
    rows = [list(CHANGE_COLUMNS)]
    for change in changes:
        if change.points is not None and abs(change.points) < threshold:
            continue
        rows.append([
            change.question,
            change.option,
            _number(change.before, decimals),
            _number(change.after, decimals),
            '' if change.points is None else f'{change.points:+.{decimals}f}',
        ])
    widths = [max(len(row[index]) for row in rows) for index in range(len(CHANGE_COLUMNS))]
    lines = ['  '.join(cell.ljust(width) if index < 2 else cell.rjust(width)
                       for index, (cell, width) in enumerate(zip(row, widths))).rstrip()
             for row in rows]
    return '\n'.join(lines) + '\n'


def _number(value, decimals):
    return '-' if value is None else f'{value:.{decimals}f}'
