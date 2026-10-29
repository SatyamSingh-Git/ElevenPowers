"""Borrowing history, rebuilt from the ledger: who had a copy, when, and how it ended."""
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Spell:
    barcode: str
    card: str
    issued: date
    ended: Optional[date] = None
    outcome: str = 'on loan'
    renewals: int = 0


def spells(entries):
    """Every loan from checkout to its end, in the order they began."""
    finished, open_spells = [], {}
    for entry in entries:
        if entry.event == 'checkout':
            open_spells[entry.barcode] = Spell(entry.barcode, entry.card, entry.date)
            finished.append(open_spells[entry.barcode])
        elif entry.event == 'renew':
            open_spells[entry.barcode].renewals += 1
        elif entry.event in ('return', 'lost'):
            spell = open_spells.pop(entry.barcode)
            spell.ended = entry.date
            spell.outcome = 'returned' if entry.event == 'return' else 'lost'
    return finished


def member_history(library, card):
    member = library.member(card)
    return [spell for spell in spells(library.ledger.entries()) if spell.card == member.card]


def copy_history(library, barcode):
    copy = library.copy(barcode)
    return [spell for spell in spells(library.ledger.entries()) if spell.barcode == copy.barcode]
