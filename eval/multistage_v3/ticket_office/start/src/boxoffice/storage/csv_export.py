"""Exports orders as CSV, one row per seat, for the finance spreadsheet."""
import csv

from ..model.money import format_pence

COLUMNS = ("order", "performance", "seat", "concession", "price", "refunded", "payment")


def export_orders(orders, path, performance=None):
    """Write `orders` to `path`, optionally only those for one performance. Returns the row count."""
    count = 0
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(COLUMNS)
        for order in sorted(orders.values(), key=lambda order: order.id):
            if performance is not None and order.performance != performance:
                continue
            for line in order.lines:
                writer.writerow([order.id, order.performance, line.seat, line.concession,
                                 format_pence(line.price), "yes" if line.refunded else "no",
                                 order.payment])
                count += 1
    return count
