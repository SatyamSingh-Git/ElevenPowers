"""The price list for the foyer board: every tier at every concession."""
from ..model.concessions import CONCESSIONS
from .formatters import Column


def price_list(performance, venue):
    """Columns and rows for `performance`: one row per tier, one money column per concession."""
    columns = [Column("tier"), *(Column(name, "money") for name in CONCESSIONS)]
    rows = []
    for tier in venue.tiers():
        face = performance.prices[tier]
        row = {"tier": tier}
        for name, percent in CONCESSIONS.items():
            row[name] = face - (face * percent + 50) // 100
        rows.append(row)
    return columns, rows
