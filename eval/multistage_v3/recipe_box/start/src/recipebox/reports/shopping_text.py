"""The printed shopping list, one heading per aisle."""
from itertools import groupby
from operator import attrgetter

from ..core.quantity import display_quantity

HEADINGS = {
    "produce": "Produce",
    "bakery": "Bakery",
    "dairy": "Dairy",
    "meat": "Meat",
    "pantry": "Pantry",
    "frozen": "Frozen",
    "other": "Other",
}

EMPTY = "Nothing to buy."


def render_shopping_list(lines):
    """Text for shopping lines that come grouped by aisle."""
    if not lines:
        return EMPTY + "\n"
    width = max(len(line.name) for line in lines) + 2
    out = [f"Shopping list: {len(lines)} items"]
    for aisle, group in groupby(lines, key=attrgetter("aisle")):
        out += ["", HEADINGS[aisle]]
        for line in group:
            amount = "" if line.quantity is None else display_quantity(line.quantity)
            out.append(f"  {line.name.ljust(width)}{amount}".rstrip())
    return "\n".join(out) + "\n"
