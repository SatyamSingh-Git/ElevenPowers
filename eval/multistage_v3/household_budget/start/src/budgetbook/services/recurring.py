"""Recurring items such as rent and salary, posted into the ledger when they fall due."""
import datetime as dt

from ..errors import ValidationError
from ..model.dates import Month, months_between
from ..model.records import FREQUENCIES, Transaction
from ..storage import files, journal
from .accounts import require_account
from .catalog import Catalog


def add_item(workspace, item):
    items = files.load_recurring(workspace)
    if any(existing.name == item.name for existing in items):
        raise ValidationError(f"recurring item already exists: {item.name}")
    require_account(workspace, item.account)
    if item.category:
        Catalog.for_workspace(workspace).require(item.category)
    if item.every not in FREQUENCIES:
        raise ValidationError(f"every must be one of: {', '.join(FREQUENCIES)}")
    if item.every == "month" and not 1 <= item.day <= 31:
        raise ValidationError("day must be between 1 and 31")
    if item.amount == 0:
        raise ValidationError("amount must not be zero")
    if item.end and item.end < item.start:
        raise ValidationError("end is before start")
    items.append(item)
    files.save_recurring(workspace, items)
    return item


def remove_item(workspace, name):
    items = files.load_recurring(workspace)
    keep = [item for item in items if item.name != name]
    if len(keep) == len(items):
        raise ValidationError(f"no recurring item called {name}")
    files.save_recurring(workspace, keep)


def due_dates(item, first, last):
    """The dates `item` falls due between `first` and `last`, both included."""
    first = max(first, item.start)
    if item.end:
        last = min(last, item.end)
    if item.every == "week":
        day = item.start
        while day <= last:
            if day >= first:
                yield day
            day += dt.timedelta(days=7)
        return
    for month in months_between(first, last):
        day = month.day(item.day)
        if first <= day <= last:
            yield day


def upcoming(workspace, first, last):
    """(date, item) for everything due between `first` and `last`, soonest first."""
    due = [(day, item) for item in files.load_recurring(workspace) for day in due_dates(item, first, last)]
    return sorted(due, key=lambda pair: (pair[0], pair[1].name))


def post_due(workspace, through):
    """Post every occurrence due up to `through` that is not in the ledger yet.

    Occurrences in closed months are left out; the month's figures are final.
    """
    posted = {(t.source, t.date) for t in journal.load_transactions(workspace.transactions_path)}
    fresh = []
    for item in files.load_recurring(workspace):
        for day in due_dates(item, item.start, through):
            if (item.source, day) in posted or workspace.is_closed(Month.of(day)):
                continue
            fresh.append(Transaction(0, day, item.account, item.payee, item.amount, item.category, "",
                                     item.source))
    if not fresh:
        return []
    return journal.append_transactions(workspace.transactions_path, fresh)
