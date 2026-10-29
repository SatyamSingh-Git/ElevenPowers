"""Moving finished years out of the transactions file.

An archived year goes to ``archive/<year>.csv`` in the transactions file's own
format, and each account's opening balance absorbs what left, so balances do
not change. Only a year whose every month is closed can be archived.
"""
from dataclasses import replace

from ..errors import ValidationError
from ..model.dates import months_of_year
from ..storage import files, journal


def archive_path(workspace, year):
    return workspace.root / "archive" / f"{year}.csv"


def archive_year(workspace, year):
    """Archive `year`; return how many transactions moved."""
    still_open = [str(month) for month in months_of_year(year) if not workspace.is_closed(month)]
    if still_open:
        raise ValidationError(f"cannot archive {year}: {still_open[0]} is not closed")
    target = archive_path(workspace, year)
    if target.exists():
        raise ValidationError(f"{year} is already archived")
    transactions = journal.load_transactions(workspace.transactions_path)
    if any(t.date.year < year for t in transactions):
        raise ValidationError(f"archive the years before {year} first")
    leaving = [t for t in transactions if t.date.year == year]
    if not leaving:
        raise ValidationError(f"no transactions in {year}")
    target.parent.mkdir(exist_ok=True)
    journal.save_transactions(target, leaving)

    moved = {}
    for transaction in leaving:
        moved[transaction.account] = moved.get(transaction.account, 0) + transaction.amount
    accounts = files.load_accounts(workspace)
    files.save_accounts(workspace, {
        name: replace(account, opening=account.opening + moved.get(name, 0)) for name, account in accounts.items()
    })
    journal.save_transactions(workspace.transactions_path, [t for t in transactions if t.date.year != year])
    return len(leaving)
