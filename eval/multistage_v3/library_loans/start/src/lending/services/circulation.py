"""Lending a copy, renewing a loan, taking a copy back, and writing off a lost one."""
from dataclasses import dataclass
from typing import Optional

from ..errors import refuse
from ..model.holds import Hold
from ..model.loans import Loan
from ..model.money import format_money
from ..storage.ledger import Entry
from . import holds, transit
from .accounts import loan_limit
from .fines import balance, fine_for
from .policy import due_date


@dataclass
class Return:
    loan: Loan
    fine: int
    hold: Optional[Hold]
    in_transit: bool


def checkout(library, card, barcode):
    today = library.today()
    member = library.member(card)
    copy = library.copy(barcode)
    if copy.barcode in library.loans:
        raise refuse('on_loan', barcode=copy.barcode)
    hold = holds.shelf_hold(library, copy.barcode)
    if hold is not None and hold.card != member.card:
        raise refuse('held_for_other', barcode=copy.barcode)
    owed = balance(library, member.card)
    if owed >= library.settings.block_at:
        raise refuse('member_blocked', card=member.card, owed=format_money(owed))
    limit = loan_limit(member.kind)
    if len(library.loans_of(member.card)) >= limit:
        raise refuse('loan_limit', card=member.card, limit=limit)
    material = library.catalogue.material_of(copy.barcode)
    loan = Loan(copy.barcode, member.card, today, due_date(library, material, today))
    library.record(Entry(today, 'checkout', loan.barcode, loan.card, loan.due, 0))
    library.loans[loan.barcode] = loan
    library.lost.discard(loan.barcode)
    if hold is not None:
        holds.collected(library, hold)
    return loan


def renew(library, barcode):
    """Renewing runs a fresh loan period from today, not from the old due date."""
    today = library.today()
    loan = library.loan(barcode.strip())
    limit = library.settings.max_renewals
    if loan.renewals >= limit:
        raise refuse('renew_limit', barcode=loan.barcode, limit=limit)
    material = library.catalogue.material_of(loan.barcode)
    loan.due = due_date(library, material, today)
    loan.renewals += 1
    library.record(Entry(today, 'renew', loan.barcode, loan.card, loan.due, 0))
    return loan


def checkin(library, barcode):
    today = library.today()
    loan = library.loan(barcode.strip())
    copy = library.copy(loan.barcode)
    material = library.catalogue.material_of(copy.barcode)
    fine = fine_for(library.settings, loan, material, copy.price, today)
    library.record(Entry(today, 'return', loan.barcode, loan.card, loan.due, fine))
    del library.loans[loan.barcode]
    hold = holds.copy_returned(library, copy.barcode)
    travelling = hold is None and transit.send_home(library, copy.barcode)
    return Return(loan, fine, hold, travelling)


def write_off(library, barcode):
    """End a loan whose copy will not come back; the member is charged the copy's price."""
    loan = library.loan(barcode.strip())
    copy = library.copy(loan.barcode)
    library.record(Entry(library.today(), 'lost', loan.barcode, loan.card, loan.due, copy.price))
    del library.loans[loan.barcode]
    library.lost.add(loan.barcode)
    return copy.price
