"""When people buy: tickets sold by hour of the day, for planning counter staff."""
from collections import Counter

from .formatters import Column

COLUMNS = [Column("hour"), Column("orders", "int"), Column("tickets", "int")]


def sales_by_hour(orders, code=None):
    """Orders and tickets by the hour they were placed, optionally for one performance.

    Only hours that sold something are listed. Refunded tickets still count:
    this is about when the counter was busy, not about what was kept.
    """
    order_counts = Counter()
    ticket_counts = Counter()
    for order in orders.values():
        if code is not None and order.performance != code:
            continue
        hour = order.created.hour
        order_counts[hour] += 1
        ticket_counts[hour] += len(order.lines)
    return [{"hour": f"{hour:02d}:00", "orders": order_counts[hour], "tickets": ticket_counts[hour]}
            for hour in sorted(order_counts)]
