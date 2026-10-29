"""The shopping list as CSV, for spreadsheets and for `pantry restock`."""
import csv
from pathlib import Path

from ..core.quantity import display_amount

COLUMNS = ("item", "quantity", "unit")


def shopping_rows(lines):
    for line in lines:
        if line.quantity is None:
            yield [line.name, "", ""]
        else:
            yield [line.name, display_amount(line.quantity.amount, line.quantity.unit), line.quantity.unit]


def write_shopping_csv(lines, path):
    """Write `lines` in the order given; returns how many rows were written."""
    rows = list(shopping_rows(lines))
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(COLUMNS)
        writer.writerows(rows)
    return len(rows)
