"""Closing a month: its figures are frozen into a month file and its transactions locked.

The month file is the record other tools read later, so its fields are
described in the reference and change only on purpose.
"""
from ..errors import ValidationError
from ..reports.month_end import summarise
from ..storage import journal
from ..storage.workspace import write_json
from .budgets import budget_status
from .catalog import Catalog

MONTH_FILE_FORMAT = 1


def close_month(workspace, month):
    if workspace.is_closed(month):
        raise ValidationError(f"month already closed: {month}")
    catalog = Catalog.for_workspace(workspace)
    in_month = [t for t in journal.load_transactions(workspace.transactions_path) if t.date in month]
    summary = summarise(in_month, catalog)
    data = {
        "format": MONTH_FILE_FORMAT,
        "month": str(month),
        "currency": workspace.settings()["currency"],
        "income": summary.income,
        "spending": summary.spending,
        "categories": [_category_entry(line, catalog) for line in budget_status(workspace, month)],
    }
    workspace.closed_dir.mkdir(exist_ok=True)
    write_json(workspace.closed_month_path(month), data)
    return data


def reopen_month(workspace, month):
    """Unlock a closed month. A later month that carried from it is not recalculated."""
    path = workspace.closed_month_path(month)
    if not path.is_file():
        raise ValidationError(f"month is not closed: {month}")
    path.unlink()


def _category_entry(line, catalog):
    return {
        "name": line.category,
        "group": catalog.group_of(line.category),
        "budget": line.budget,
        "carried": line.carried,
        "spent": line.spent,
        "remaining": line.remaining,
    }
