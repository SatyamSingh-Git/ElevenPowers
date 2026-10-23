from dataclasses import dataclass
from decimal import Decimal

from .money import format_money

AMOUNTS = ("subtotal", "discount", "tax", "total")


@dataclass
class LedgerRow:
    region: str
    currency: str
    invoices: int = 0
    subtotal: Decimal = Decimal(0)
    discount: Decimal = Decimal(0)
    tax: Decimal = Decimal(0)
    total: Decimal = Decimal(0)


def summarize(records):
    """One row per region and currency, in that order, adding up exported invoice records."""
    rows = {}
    for record in records:
        key = (record["region"], record["currency"])
        row = rows.setdefault(key, LedgerRow(*key))
        row.invoices += 1
        for name in AMOUNTS:
            setattr(row, name, getattr(row, name) + Decimal(record[name]))
    return [rows[key] for key in sorted(rows)]


def render_ledger(rows):
    header = (f"{'Region':<8}{'Cur':<5}{'Invoices':>9}"
              f"{'Subtotal':>16}{'Discount':>16}{'Tax':>16}{'Total':>16}")
    out = [header, "-" * len(header)]
    for row in rows:
        amounts = [row.subtotal, -row.discount, row.tax, row.total]
        out.append(f"{row.region:<8}{row.currency:<5}{row.invoices:>9}"
                   + "".join(f"{format_money(amount, row.currency):>16}" for amount in amounts))
    return "\n".join(out) + "\n"
