"""The loans ledger: an append-only record of every circulation event.

The file is plain text so that staff and finance can read it. Its first line
names the format; every other line is one event, with tab-separated fields

    date  event  barcode  card  due  amount

An empty field is written as '-'. Amounts are pounds with two decimals.
Nothing in the ledger is ever rewritten; current loans are worked out by
reading it from the top.
"""
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional

from ..errors import LendingError, refuse
from ..model.dates import format_date, parse_date
from ..model.money import parse_money, plain_amount

FILE = 'loans.ledger'
HEADER = '#lending-ledger v1'
FIELDS = ('date', 'event', 'barcode', 'card', 'due', 'amount')
EVENTS = ('checkout', 'renew', 'return', 'lost', 'payment', 'waive')
EMPTY = '-'
SEPARATOR = '\t'


@dataclass(frozen=True)
class Entry:
    date: date
    event: str
    barcode: Optional[str]
    card: Optional[str]
    due: Optional[date]
    amount: int


class Ledger:
    def __init__(self, path):
        self.path = Path(path)

    def append(self, entry):
        fresh = not self.path.exists()
        with self.path.open('a', encoding='utf-8', newline='\n') as out:
            if fresh:
                out.write(HEADER + '\n')
            out.write(format_line(entry) + '\n')

    def entries(self):
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding='utf-8').splitlines()
        _check_header(self.path, lines[0] if lines else '')
        return [parse_line(self.path, number, line)
                for number, line in enumerate(lines[1:], 2) if line.strip()]


def _check_header(path, line):
    if line != HEADER:
        raise refuse('bad_ledger', path=path.name, line=1, problem=f'expected {HEADER}')


def format_line(entry):
    cells = (format_date(entry.date), entry.event, entry.barcode or EMPTY, entry.card or EMPTY,
             format_date(entry.due) if entry.due else EMPTY, plain_amount(entry.amount))
    return SEPARATOR.join(cells)


def parse_line(path, number, line):
    cells = line.split(SEPARATOR)
    if len(cells) != len(FIELDS):
        raise refuse('bad_ledger', path=path.name, line=number, problem=f'{len(cells)} fields, not {len(FIELDS)}')
    day, event, barcode, card, due, amount = cells
    if event not in EVENTS:
        raise refuse('bad_ledger', path=path.name, line=number, problem=f'unknown event {event}')
    try:
        return Entry(parse_date(day), event, _optional(barcode), _optional(card),
                     parse_date(due) if due != EMPTY else None, parse_money(amount))
    except LendingError as error:
        raise refuse('bad_ledger', path=path.name, line=number, problem=error.message) from None


def _optional(cell):
    return None if cell == EMPTY else cell
