"""The month-end report: income, spending by category and the biggest payees."""
from dataclasses import dataclass

from ..services.catalog import UNCATEGORISED
from .render import Report, Section

TOP_PAYEES = 5


@dataclass(frozen=True)
class MonthSummary:
    income: int
    spending: int
    categories: list
    payees: list

    @property
    def net(self):
        return self.income - self.spending


def summarise(transactions, catalog):
    """Income and spending of `transactions`; categories and payees biggest first."""
    income = 0
    by_category, by_payee = {}, {}
    for transaction in transactions:
        if catalog.is_income(transaction.category):
            income += transaction.amount
        elif transaction.amount < 0 and catalog.is_spending(transaction.category):
            name = transaction.category or UNCATEGORISED
            by_category[name] = by_category.get(name, 0) - transaction.amount
            by_payee[transaction.payee] = by_payee.get(transaction.payee, 0) - transaction.amount
    return MonthSummary(income, sum(by_category.values()), _biggest_first(by_category),
                        _biggest_first(by_payee))


def _biggest_first(totals):
    return sorted(totals.items(), key=lambda item: (-item[1], item[0]))


def month_report(month, transactions, catalog, currency):
    summary = summarise([t for t in transactions if t.date in month], catalog)
    return Report(f"Month end {month} ({currency})", [
        Section("Summary", ("Item", "Amount"),
                [("Income", summary.income), ("Spending", summary.spending), ("Net", summary.net)],
                amounts=("Amount",)),
        Section("Spending by category", ("Category", "Amount"), summary.categories, amounts=("Amount",)),
        Section("Top payees", ("Payee", "Amount"), summary.payees[:TOP_PAYEES], amounts=("Amount",)),
    ])
