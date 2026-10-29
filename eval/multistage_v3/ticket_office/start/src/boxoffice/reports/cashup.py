"""End-of-day cash-up: what each payment method should account for."""
from ..services.sales import PAYMENT_METHODS
from .formatters import Column

COLUMNS = [Column("payment"), Column("entries", "int"), Column("amount", "money")]


def cashup(entries):
    """One row per payment method, with the number of ledger entries and their sum.

    Every accepted method gets a row, even one that took nothing, so the
    person cashing up sees a zero rather than wondering about a missing line.
    """
    counts = {method: 0 for method in PAYMENT_METHODS}
    amounts = {method: 0 for method in PAYMENT_METHODS}
    for entry in entries:
        method = entry["payment"]
        counts[method] = counts.get(method, 0) + 1
        amounts[method] = amounts.get(method, 0) + entry["amount"]
    rows = [{"payment": method, "entries": counts[method], "amount": amounts[method]} for method in counts]
    rows.append({"payment": "total", "entries": sum(counts.values()), "amount": sum(amounts.values())})
    return rows
