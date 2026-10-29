"""Overdue fines and payments.

What a member owes is never stored: it is read off the ledger, charges less
payments, so the ledger stays the single record finance reconciles against.
"""
from dataclasses import dataclass
from datetime import date

from ..errors import refuse
from ..model.dates import days_late
from ..model.money import format_money
from ..storage.ledger import Entry
from .policy import daily_fine


@dataclass
class Line:
    date: date
    description: str
    amount: int
    owed: int


def fine_for(settings, loan, material, price, returned_on):
    """The charge for returning `loan` on `returned_on`.

    A daily rate for every day past the due date, capped at `max_fine` and at
    the price of the copy, since nobody should owe more than a replacement.
    """
    late = days_late(loan.due, returned_on)
    if late <= 0:
        return 0
    return min(late * daily_fine(settings, material), settings.max_fine, price)


CHARGES = {'return': 'fine on', 'lost': 'replacing'}
CREDITS = {'payment': 'payment', 'waive': 'waived'}


def signed_amount(entry):
    """What a ledger entry adds to a member's debt: charges count up, payments and waivers down."""
    if entry.event in CHARGES:
        return entry.amount
    if entry.event in CREDITS:
        return -entry.amount
    return 0


def balance(library, card):
    member = library.member(card)
    return sum(signed_amount(entry) for entry in library.ledger.entries() if entry.card == member.card)


def statement(library, card):
    """Every charge and payment for a member, oldest first, with what was owed after each."""
    member = library.member(card)
    lines, owed = [], 0
    for entry in library.ledger.entries():
        amount = signed_amount(entry) if entry.card == member.card else 0
        if amount == 0:
            continue
        owed += amount
        what = CHARGES.get(entry.event) or CREDITS[entry.event]
        if entry.barcode:
            what += f' {entry.barcode}'
        lines.append(Line(entry.date, what, amount, owed))
    return lines


def pay(library, card, amount):
    """Record a payment of `amount` pence; returns what is still owed."""
    member = library.member(card)
    if amount <= 0:
        raise refuse('bad_amount', text=format_money(amount))
    library.record(Entry(library.today(), 'payment', None, member.card, None, amount))
    return balance(library, member.card)


def waive(library, card, amount):
    """Write off part or all of what a member owes, at a manager's discretion."""
    member = library.member(card)
    owed = balance(library, member.card)
    if amount <= 0 or amount > owed:
        raise refuse('bad_waiver', amount=format_money(amount), card=member.card, owed=format_money(owed))
    library.record(Entry(library.today(), 'waive', None, member.card, None, amount))
    return owed - amount


def amnesty(library, charged_before):
    """Waive everything still owed for charges made before `charged_before`, member by member.

    Payments are taken to clear the oldest charges first, so only what is left
    of the older charges is waived. Returns the amount waived per card.
    """
    entries = library.ledger.entries()
    waived = {}
    for card in sorted(library.members):
        old, paid = 0, 0
        for entry in entries:
            if entry.card != card:
                continue
            amount = signed_amount(entry)
            if amount > 0 and entry.date < charged_before:
                old += amount
            elif amount < 0:
                paid -= amount
        owed = min(old - paid, balance(library, card))
        if owed > 0:
            library.record(Entry(library.today(), 'waive', None, card, None, owed))
            waived[card] = owed
    return waived
