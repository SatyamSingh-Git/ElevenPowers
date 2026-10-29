"""Importing a bank statement into one account.

A statement usually overlaps the previous one by a few days, so rows that are
already in the account are skipped rather than added twice.
"""
from collections import Counter
from dataclasses import dataclass, field

from ..errors import StatementError
from ..importers import detect_layout, get_layout
from ..importers.base import Problem
from ..model.dates import Month
from ..model.records import Transaction
from ..rules.engine import RuleBook
from ..storage import files, journal
from .accounts import require_account


@dataclass
class ImportResult:
    layout: str
    added: list = field(default_factory=list)
    duplicates: int = 0
    problems: list = field(default_factory=list)


def import_statement(workspace, account, text, layout=None, dry_run=False):
    """Add the statement's new rows to `account`. With `dry_run`, work out the result but store nothing."""
    require_account(workspace, account)
    chosen = get_layout(layout) if layout else detect_layout(text)
    rows, problems = chosen.read(text)
    if not rows and not problems:
        raise StatementError("the statement has no transactions")
    book = RuleBook(files.load_rules(workspace))
    stored = journal.load_transactions(workspace.transactions_path)
    # Counted rather than a set: two identical coffees on one day are two transactions.
    already = Counter(_identity(t.date, t.amount, t.payee) for t in stored if t.account == account)
    result = ImportResult(chosen.name, problems=list(problems))
    fresh = []
    for row in rows:
        month = Month.of(row.date)
        if workspace.is_closed(month):
            result.problems.append(Problem(row.line, f"month is closed: {month}"))
            continue
        identity = _identity(row.date, row.amount, row.payee)
        if already[identity]:
            already[identity] -= 1
            result.duplicates += 1
            continue
        category = book.category_for(row.payee, account)
        fresh.append(Transaction(0, row.date, account, row.payee, row.amount, category, row.memo,
                                 f"import:{chosen.name}"))
    if dry_run:
        result.added = fresh
    elif fresh:
        result.added = journal.append_transactions(workspace.transactions_path, fresh)
    return result


def _identity(day, amount, payee):
    return day, amount, payee.casefold()
