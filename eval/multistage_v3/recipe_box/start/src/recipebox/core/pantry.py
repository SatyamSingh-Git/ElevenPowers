"""The pantry: what is already in the kitchen.

An item either has a quantity or is a staple (no quantity), which means there
is always enough of it.
"""
from dataclasses import dataclass

from . import units
from .ingredients import canonical_name
from .quantity import Quantity
from ..errors import PantryError, RecipeBoxError


@dataclass(frozen=True)
class PantryItem:
    name: str
    quantity: Quantity | None = None

    @property
    def staple(self):
        return self.quantity is None


class Pantry:
    def __init__(self, items=()):
        self._items = {}
        for item in items:
            self._items[item.name] = item

    def get(self, name):
        return self._items.get(canonical_name(name))

    def add(self, name, quantity=None):
        """Add to what is held. Adding without a quantity makes the item a staple."""
        name = canonical_name(name)
        held = self._items.get(name)
        if held is not None and held.staple:
            return held
        if quantity is None or held is None:
            self._items[name] = PantryItem(name, quantity)
            return self._items[name]
        try:
            extra = units.convert(quantity.amount, quantity.unit, held.quantity.unit)
        except RecipeBoxError as error:
            raise PantryError(f"{name}: {error}") from error
        self._items[name] = PantryItem(name, Quantity(held.quantity.amount + extra, held.quantity.unit))
        return self._items[name]

    def use(self, name, quantity):
        """Take `quantity` out; the item goes once nothing is left."""
        name = canonical_name(name)
        held = self._items.get(name)
        if held is None:
            raise PantryError(f"{name} is not in the pantry")
        if held.staple:
            return
        left = held.quantity.amount - units.convert(quantity.amount, quantity.unit, held.quantity.unit)
        if left <= 0:
            del self._items[name]
        else:
            self._items[name] = PantryItem(name, Quantity(left, held.quantity.unit))

    def remove(self, name):
        name = canonical_name(name)
        if name not in self._items:
            raise PantryError(f"{name} is not in the pantry")
        del self._items[name]

    def restock(self, purchases):
        """Add every (name, quantity) bought; returns how many lines were added."""
        count = 0
        for name, quantity in purchases:
            self.add(name, quantity)
            count += 1
        return count

    def items(self):
        return [self._items[name] for name in sorted(self._items)]

    def __contains__(self, name):
        return canonical_name(name) in self._items

    def __len__(self):
        return len(self._items)
