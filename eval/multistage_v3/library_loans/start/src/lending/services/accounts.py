"""A member's account at a glance: what they have, what they owe, what they may take."""
from dataclasses import dataclass

from ..model.holds import READY
from .fines import balance

LOAN_LIMITS = {'adult': 20, 'child': 10}


def loan_limit(kind):
    return LOAN_LIMITS[kind]


@dataclass
class Summary:
    card: str
    name: str
    kind: str
    on_loan: int
    overdue: int
    holds_waiting: int
    holds_ready: int
    owed: int
    can_borrow: int


def summary(library, card):
    member = library.member(card)
    today = library.today()
    loans = library.loans_of(member.card)
    held = library.holds_of(member.card)
    ready = sum(hold.status == READY for hold in held)
    return Summary(
        card=member.card,
        name=member.name,
        kind=member.kind,
        on_loan=len(loans),
        overdue=sum(loan.is_overdue(today) for loan in loans),
        holds_waiting=len(held) - ready,
        holds_ready=ready,
        owed=balance(library, member.card),
        can_borrow=max(0, loan_limit(member.kind) - len(loans)),
    )
