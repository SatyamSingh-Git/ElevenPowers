"""Monthly budgets per category, and how a month is going against them.

A budget with rollover starts each month with whatever it had left when the
previous month was closed; an overspend is carried as a negative amount.
"""
from dataclasses import dataclass

from ..errors import NotFound, ValidationError
from ..model.money import decimal_text
from ..model.records import BudgetLine
from ..storage import files, journal
from ..storage.workspace import read_json
from .catalog import Catalog


@dataclass(frozen=True)
class StatusLine:
    category: str
    budget: int
    carried: int
    spent: int

    @property
    def available(self):
        return self.budget + self.carried

    @property
    def remaining(self):
        return self.available - self.spent


def set_budget(workspace, category, amount, rollover=False):
    Catalog.for_workspace(workspace).require(category)
    if amount < 0:
        raise ValidationError(f"budget must not be negative: {decimal_text(amount)}")
    budgets = files.load_budgets(workspace)
    budgets[category] = BudgetLine(category, amount, rollover)
    files.save_budgets(workspace, budgets)
    return budgets[category]


def remove_budget(workspace, category):
    budgets = files.load_budgets(workspace)
    if category not in budgets:
        raise NotFound(f"no budget for {category}")
    del budgets[category]
    files.save_budgets(workspace, budgets)


def suggest(workspace, month, count=3):
    """A budget per category: average monthly spending over the `count` months before `month`.

    Averages are rounded up to the next whole unit, since a budget a little too
    generous is easier to live with than one a little too tight.
    """
    catalog = Catalog.for_workspace(workspace)
    months = [month.previous()]
    while len(months) < count:
        months.append(months[-1].previous())
    transactions = [t for t in journal.load_transactions(workspace.transactions_path)
                    if any(t.date in earlier for earlier in months)]
    totals = _spent_by_category(transactions, catalog)
    return {name: -(-total // (count * 100)) * 100 for name, total in sorted(totals.items())
            if name and total > 0}


def budget_status(workspace, month):
    """One line per budgeted category, in category order."""
    catalog = Catalog.for_workspace(workspace)
    in_month = [t for t in journal.load_transactions(workspace.transactions_path) if t.date in month]
    spent = _spent_by_category(in_month, catalog)
    carried = _carried_into(workspace, month)
    return [
        StatusLine(name, line.amount, carried.get(name, 0) if line.rollover else 0, spent.get(name, 0))
        for name, line in files.load_budgets(workspace).items()
    ]


def _spent_by_category(transactions, catalog):
    spent = {}
    for transaction in transactions:
        if transaction.amount < 0 and catalog.is_spending(transaction.category):
            spent[transaction.category] = spent.get(transaction.category, 0) - transaction.amount
    return spent


def _carried_into(workspace, month):
    """What each category had left when the month before `month` was closed."""
    closed = read_json(workspace.closed_month_path(month.previous()), None)
    if closed is None:
        return {}
    return {entry["name"]: entry["remaining"] for entry in closed["categories"]}
