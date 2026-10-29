"""Which recipes the pantry can already cook."""
from dataclasses import dataclass, field

from ..core import units


@dataclass
class Readiness:
    recipe: object
    # Names of ingredients the pantry lacks or holds too little of.
    short: list = field(default_factory=list)

    @property
    def ready(self):
        return not self.short


def _enough(held, quantity):
    if held.staple or quantity is None:
        return True
    if held.quantity is None or not units.convertible(held.quantity.unit, quantity.unit):
        return False
    return units.convert(held.quantity.amount, held.quantity.unit, quantity.unit) >= quantity.amount


def readiness(recipe, pantry):
    short = []
    for ingredient in recipe.ingredients:
        held = pantry.get(ingredient.name)
        if held is None or not _enough(held, ingredient.quantity):
            short.append(ingredient.name)
    return Readiness(recipe, short)


def cookable(library, pantry, missing=0):
    """Recipes short of at most `missing` ingredients, fewest short first, then by title."""
    found = [readiness(recipe, pantry) for recipe in library]
    found = [entry for entry in found if len(entry.short) <= missing]
    found.sort(key=lambda entry: (len(entry.short), entry.recipe.title.lower()))
    return found
