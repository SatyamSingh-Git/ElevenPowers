"""The door list for front of house: who sits where, in seat-map order."""
from .formatters import Column

COLUMNS = [Column("seat"), Column("concession"), Column("order"), Column("customer")]


def door_list(venue, orders, customers, code):
    """One row per seat sold for performance `code`. `customers` maps email to Customer."""
    position = venue.seat_order()
    rows = []
    for order in orders.values():
        if order.performance != code:
            continue
        name = customers[order.customer].name if order.customer in customers else ""
        for line in order.active_lines():
            rows.append({"seat": line.seat, "concession": line.concession, "order": order.id, "customer": name})
    rows.sort(key=lambda row: position[row["seat"]])
    return rows
