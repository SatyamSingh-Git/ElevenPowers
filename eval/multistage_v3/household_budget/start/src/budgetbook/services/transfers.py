"""Spotting money moved between the household's own accounts.

A transfer shows up twice: money out of one account and the same amount into
another a day or two later. Filed under the Transfer category, both halves
drop out of income and spending.
"""
from dataclasses import dataclass, replace

from ..model.dates import Month
from ..storage import journal

TRANSFER_CATEGORY = "Transfer"
MAX_DAYS_APART = 3


@dataclass(frozen=True)
class TransferPair:
    out: object
    into: object

    @property
    def days_apart(self):
        return (self.into.date - self.out.date).days


def find_pairs(transactions):
    """Uncategorised out/in pairs between two accounts, each transaction in at most one pair.

    Outgoing halves are taken oldest first and matched with the closest
    incoming half, so the result does not depend on the order of the file.
    """
    candidates = [t for t in transactions if t.uncategorised]
    outgoing = sorted((t for t in candidates if t.amount < 0), key=lambda t: (t.date, t.id))
    incoming = sorted((t for t in candidates if t.amount > 0), key=lambda t: (t.date, t.id))
    used, pairs = set(), []
    for out in outgoing:
        matches = [
            into for into in incoming
            if into.id not in used and into.account != out.account and into.amount == -out.amount
            and 0 <= (into.date - out.date).days <= MAX_DAYS_APART
        ]
        if matches:
            into = min(matches, key=lambda t: ((t.date - out.date).days, t.id))
            used.add(into.id)
            pairs.append(TransferPair(out, into))
    return pairs


def file_transfers(workspace):
    """File every pair found in open months as a transfer; return the pairs filed."""
    transactions = journal.load_transactions(workspace.transactions_path)
    pairs = [pair for pair in find_pairs(transactions)
             if not workspace.is_closed(Month.of(pair.out.date))
             and not workspace.is_closed(Month.of(pair.into.date))]
    if not pairs:
        return []
    ids = {t.id for pair in pairs for t in (pair.out, pair.into)}
    filed = [replace(t, category=TRANSFER_CATEGORY) if t.id in ids else t for t in transactions]
    journal.save_transactions(workspace.transactions_path, filed)
    return pairs
