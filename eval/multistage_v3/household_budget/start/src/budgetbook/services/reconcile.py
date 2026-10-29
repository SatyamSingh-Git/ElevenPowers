"""Checking the books against the balance a bank statement shows."""
from dataclasses import dataclass
import datetime as dt

from ..storage import journal
from .accounts import require_account


@dataclass(frozen=True)
class Reconciliation:
    account: str
    on: dt.date
    books: int
    statement: int
    candidates: list

    @property
    def difference(self):
        return self.statement - self.books

    @property
    def agrees(self):
        return self.difference == 0


def reconcile(workspace, account_name, on, statement_balance, window_days=7):
    """Compare the books with `statement_balance` at the end of `on`.

    When they differ, transactions from the last `window_days` days whose
    amount equals the difference, or its opposite, are the usual suspects: a
    payment entered twice, or one the bank has not taken yet.
    """
    account = require_account(workspace, account_name)
    mine = [t for t in journal.load_transactions(workspace.transactions_path) if t.account == account.name]
    books = account.opening + sum(t.amount for t in mine if t.date <= on)
    difference = statement_balance - books
    since = on - dt.timedelta(days=window_days)
    candidates = []
    if difference:
        candidates = [t for t in mine if since < t.date <= on and abs(t.amount) == abs(difference)]
        candidates.sort(key=lambda t: (t.date, t.id))
    return Reconciliation(account.name, on, books, statement_balance, candidates)
