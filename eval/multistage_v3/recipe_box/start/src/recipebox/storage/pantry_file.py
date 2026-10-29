"""The pantry file, `pantry.csv`, and reading back a shopping list that was bought.

`pantry.csv` has the columns item, amount, unit. A blank amount marks a staple.
"""
import csv
from pathlib import Path

from ..core import units
from ..core.pantry import Pantry, PantryItem
from ..core.quantity import Quantity, format_amount, parse_amount
from ..errors import PantryError, RecipeBoxError

PANTRY_HEADER = ("item", "amount", "unit")


def _quantity(amount, unit, where):
    if not amount.strip():
        return None
    try:
        return Quantity(parse_amount(amount), units.unit(unit).symbol)
    except RecipeBoxError as error:
        raise PantryError(f"{where}: {error}") from error


def load_pantry(path):
    """The pantry saved at `path`; a missing file is an empty pantry."""
    path = Path(path)
    if not path.is_file():
        return Pantry()
    items = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != PANTRY_HEADER:
            raise PantryError(f"{path.name}: expected the header {','.join(PANTRY_HEADER)}")
        for row in reader:
            where = f"{path.name} line {reader.line_num}"
            items.append(PantryItem(row["item"], _quantity(row["amount"], row["unit"], where)))
    return Pantry(items)


def save_pantry(pantry, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(PANTRY_HEADER)
        for item in pantry.items():
            if item.staple:
                writer.writerow([item.name, "", ""])
            else:
                writer.writerow([item.name, format_amount(item.quantity.amount), item.quantity.unit])


def read_purchases(path):
    """(name, quantity) for each line of a shopping list saved with `shop --csv`."""
    path = Path(path)
    purchases = []
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    for number, row in enumerate(rows[1:], 2):
        if not row:
            continue
        name, amount, unit = row
        purchases.append((name, _quantity(amount, unit, f"{path.name} line {number}")))
    return purchases
