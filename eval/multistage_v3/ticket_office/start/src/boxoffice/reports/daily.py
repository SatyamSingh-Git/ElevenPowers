"""Takings per day, worked out from the ledger."""
from .formatters import Column

COLUMNS = [
    Column("day"),
    Column("sold", "int"),
    Column("returned", "int"),
    Column("sales", "money"),
    Column("refunds", "money"),
    Column("net", "money"),
]


class _Day:
    """One day's running totals; each ledger kind has its own `_on_<kind>` method."""

    def __init__(self, day):
        self.day = day
        self.sold = 0
        self.returned = 0
        self.sales = 0
        self.refunds = 0

    def add(self, entry):
        getattr(self, "_on_" + entry["kind"])(entry)

    def _on_sale(self, entry):
        self.sold += entry["tickets"]
        self.sales += entry["amount"]

    def _on_refund(self, entry):
        self.returned += entry["tickets"]
        self.refunds -= entry["amount"]

    def row(self):
        return {"day": self.day, "sold": self.sold, "returned": self.returned,
                "sales": self.sales, "refunds": self.refunds, "net": self.sales - self.refunds}


def daily_takings(entries, day=None):
    """One row per day that has entries, oldest first; only `day` (YYYY-MM-DD) when given."""
    days = {}
    for entry in entries:
        when = entry["date"]
        if day is not None and when != day:
            continue
        if when not in days:
            days[when] = _Day(when)
        days[when].add(entry)
    return [days[when].row() for when in sorted(days)]


def totals(rows):
    """A last row adding up every day in `rows`."""
    summed = {"day": "total"}
    for column in COLUMNS[1:]:
        summed[column.name] = sum(row[column.name] for row in rows)
    return summed
