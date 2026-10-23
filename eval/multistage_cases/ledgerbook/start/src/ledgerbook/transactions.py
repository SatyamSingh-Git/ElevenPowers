"""Balanced transactions built from postings in integer minor units.

A posting's amount is signed: debits are positive, credits negative. A
transaction is accepted only when its postings sum to zero.
"""
from dataclasses import dataclass
import datetime
import re

from .errors import LedgerError, UnbalancedError

MIN_POSTINGS = 2
MAX_POSTINGS = 16
MAX_DESCRIPTION = 120

_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


@dataclass(frozen=True)
class Posting:
    account: str
    amount: int


@dataclass(frozen=True)
class Transaction:
    date: str
    description: str
    postings: tuple

    @property
    def accounts(self):
        """Accounts this transaction touches, in posting order, each once."""
        return tuple(dict.fromkeys(posting.account for posting in self.postings))

    def touches(self, account):
        return any(posting.account == account for posting in self.postings)

    def amount_for(self, account):
        return sum(posting.amount for posting in self.postings if posting.account == account)


def check_date(value):
    """Return `value` if it is a real calendar date written YYYY-MM-DD."""
    if not isinstance(value, str) or not _ISO_DATE.fullmatch(value):
        raise LedgerError(f"invalid date: {value}")
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        raise LedgerError(f"invalid date: {value}") from None
    return value


def make_transaction(date, description, postings):
    """Build a Transaction from (account, amount) pairs or Posting objects.

    Raises LedgerError for a bad date, description or posting count, and
    UnbalancedError when the amounts do not sum to zero.
    """
    check_date(date)
    if not 1 <= len(description) <= MAX_DESCRIPTION:
        raise LedgerError(f"description must be 1 to {MAX_DESCRIPTION} characters")
    postings = tuple(p if isinstance(p, Posting) else Posting(*p) for p in postings)
    if len(postings) < MIN_POSTINGS:
        raise LedgerError(f"transaction needs at least {MIN_POSTINGS} postings")
    if len(postings) > MAX_POSTINGS:
        raise LedgerError(f"transaction has more than {MAX_POSTINGS} postings")
    for posting in postings:
        if type(posting.amount) is not int:
            raise LedgerError(f"posting amount must be an integer: {posting.amount!r}")
    difference = sum(posting.amount for posting in postings)
    if difference:
        raise UnbalancedError(f"transaction does not balance: off by {difference}")
    return Transaction(date, description, postings)


def reversal(txn, date, description=None):
    """A transaction on `date` that exactly undoes `txn`."""
    description = description or f"Reversal: {txn.description}"[:MAX_DESCRIPTION]
    return make_transaction(date, description, [(p.account, -p.amount) for p in txn.postings])
