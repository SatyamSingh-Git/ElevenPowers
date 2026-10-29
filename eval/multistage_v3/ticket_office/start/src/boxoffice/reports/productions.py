"""Sales by production: every performance of a title added together."""
from collections import defaultdict

from ..clock import format_time
from .formatters import Column

COLUMNS = [
    Column("title"),
    Column("performances", "int"),
    Column("first"),
    Column("last"),
    Column("sold", "int"),
    Column("occupancy", "percent"),
    Column("face", "money"),
]


def production_summary(performances, orders, capacity):
    """One row per title, in the order the productions open. Cancelled performances are left out."""
    sold = defaultdict(int)
    face = defaultdict(int)
    for order in orders.values():
        for line in order.active_lines():
            sold[order.performance] += 1
            face[order.performance] += line.price
    runs = defaultdict(list)
    for performance in performances.values():
        if not performance.cancelled:
            runs[performance.title].append(performance)
    rows = []
    for title, run in sorted(runs.items(), key=lambda item: min(p.starts for p in item[1])):
        run.sort(key=lambda performance: performance.starts)
        seats = sum(sold[performance.code] for performance in run)
        rows.append({"title": title, "performances": len(run),
                     "first": format_time(run[0].starts)[:10], "last": format_time(run[-1].starts)[:10],
                     "sold": seats, "occupancy": round(100 * seats / (capacity * len(run)), 1),
                     "face": sum(face[performance.code] for performance in run)})
    return rows
