"""How full a performance is, section by section."""
from collections import Counter

from .formatters import Column

COLUMNS = [Column("section"), Column("capacity", "int"), Column("sold", "int"), Column("occupancy", "percent")]


def occupancy(venue, orders, code):
    """Seats sold for performance `code` in each section, and the house as a whole."""
    sold = Counter()
    for order in orders.values():
        if order.performance != code:
            continue
        for line in order.active_lines():
            sold[venue.seat(line.seat).section] += 1
    rows = [_row(section.name, section.capacity, sold[section.name]) for section in venue.sections]
    rows.append(_row("all", venue.capacity, sum(sold.values())))
    return rows


def _row(name, capacity, sold):
    share = round(100 * sold / capacity, 1) if capacity else 0.0
    return {"section": name, "capacity": capacity, "sold": sold, "occupancy": share}
