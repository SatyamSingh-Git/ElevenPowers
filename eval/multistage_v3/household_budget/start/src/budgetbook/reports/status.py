"""The budget status table for one month."""
from ..model.money import share
from .render import Report, Section


def status_report(month, lines, currency):
    rows = []
    for line in lines:
        used = share(line.spent, line.available)
        rows.append((line.category, line.budget, line.carried, line.spent, line.remaining,
                     "-" if used is None else f"{used}%"))
    totals = ("Total", sum(line.budget for line in lines), sum(line.carried for line in lines),
              sum(line.spent for line in lines), sum(line.remaining for line in lines), "")
    return Report(f"Budget status {month} ({currency})", [
        Section("Budgets", ("Category", "Budget", "Carried", "Spent", "Remaining", "Used"),
                rows + [totals] if rows else [], amounts=("Budget", "Carried", "Spent", "Remaining")),
    ])
