"""Which concessions a performance sold, for the marketing team."""
from collections import Counter

from .formatters import Column

COLUMNS = [Column("concession"), Column("tickets", "int"), Column("share", "percent"), Column("face", "money")]


def concession_mix(orders, code):
    """Tickets still sold for `code` by concession, most popular first."""
    tickets = Counter()
    face = Counter()
    for order in orders.values():
        if order.performance != code:
            continue
        for line in order.active_lines():
            tickets[line.concession] += 1
            face[line.concession] += line.price
    total = sum(tickets.values())
    return [{"concession": name, "tickets": count, "share": round(100 * count / total, 1), "face": face[name]}
            for name, count in sorted(tickets.items(), key=lambda item: (-item[1], item[0]))]
