"""How spending in each category moved over the last few months."""
from ..model.dates import Month
from .month_end import summarise
from .render import Report, Section


def spending_trend(last_month, count, transactions, catalog, currency):
    """Spending per category for `count` months ending with `last_month`, oldest month first."""
    months = [last_month]
    while len(months) < count:
        months.insert(0, months[0].previous())
    by_month = {month: [] for month in months}
    for transaction in transactions:
        month = Month.of(transaction.date)
        if month in by_month:
            by_month[month].append(transaction)
    spending = {month: dict(summarise(by_month[month], catalog).categories) for month in months}
    names = sorted({name for totals in spending.values() for name in totals})
    rows = []
    for name in names:
        amounts = [spending[month].get(name, 0) for month in months]
        rows.append((name, *amounts, sum(amounts) // len(months)))
    columns = ("Category", *(str(month) for month in months), "Average")
    return Report(f"Spending trend to {last_month} ({currency})", [
        Section("Categories", columns, rows, amounts=columns[1:]),
    ])
