"""The season at a glance: every performance with its sales and how full it is."""
from collections import Counter

from ..clock import format_time
from .formatters import Column

COLUMNS = [
    Column("code"),
    Column("title"),
    Column("starts"),
    Column("sold", "int"),
    Column("occupancy", "percent"),
    Column("face", "money"),
]


def season_summary(performances, orders, capacity):
    """One row per performance in date order; `face` is the value of the seats still sold."""
    sold = Counter()
    face = Counter()
    for order in orders.values():
        for line in order.active_lines():
            sold[order.performance] += 1
            face[order.performance] += line.price
    rows = []
    for performance in sorted(performances.values(), key=lambda performance: performance.starts):
        code = performance.code
        title = performance.title + (" (cancelled)" if performance.cancelled else "")
        rows.append({"code": code, "title": title, "starts": format_time(performance.starts),
                     "sold": sold[code], "occupancy": round(100 * sold[code] / capacity, 1),
                     "face": face[code]})
    return rows
