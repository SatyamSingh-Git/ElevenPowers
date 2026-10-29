"""The year at a glance, read from the month files written when each month was closed.

Only closed months appear: an open month's figures can still change.
"""
from ..model.dates import months_of_year
from ..storage.workspace import read_json
from .render import Report, Section


def year_report(workspace, year, currency):
    months, spent = [], {}
    for month in months_of_year(year):
        closed = read_json(workspace.closed_month_path(month), None)
        if closed is None:
            continue
        income, spending = closed["income"], closed["spending"]
        months.append((str(month), income, spending, income - spending))
        for entry in closed["categories"]:
            spent[entry["name"]] = spent.get(entry["name"], 0) + entry["spent"]
    total = ("Total", sum(row[1] for row in months), sum(row[2] for row in months),
             sum(row[3] for row in months))
    return Report(f"Year {year} ({currency})", [
        Section("Months", ("Month", "Income", "Spending", "Net"), months + [total],
                amounts=("Income", "Spending", "Net")),
        Section("Budgeted categories", ("Category", "Spent"), sorted(spent.items()), amounts=("Spent",)),
    ])
