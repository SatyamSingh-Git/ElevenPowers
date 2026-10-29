"""Standing in for an ingredient you do not have."""
from dataclasses import dataclass
from fractions import Fraction

from ..core.ingredients import Ingredient
from ..core.quantity import Quantity
from ..errors import RecipeBoxError


@dataclass(frozen=True)
class Swap:
    # What replaces one unit of the original, as (name, amount per unit, unit or None to keep the original's).
    parts: tuple
    hint: str = ""


SWAPS = {
    "buttermilk": Swap((("milk", Fraction(1), None), ("lemon juice", Fraction(1, 16), None)),
                       "stir and leave for 5 minutes"),
    "self-raising flour": Swap((("flour", Fraction(1), None), ("baking powder", Fraction(1, 24), None))),
    "cream": Swap((("milk", Fraction(3, 4), None), ("butter", Fraction(1, 4), None))),
    "honey": Swap((("sugar", Fraction(5, 4), None),), "add a little more liquid"),
    "egg": Swap((("banana", Fraction(1, 2), ""),), "for baking only"),
    "green onion": Swap((("onion", Fraction(1, 2), None),)),
    "yogurt": Swap((("cream", Fraction(1), None), ("lemon juice", Fraction(1, 16), None))),
}


def substitute(ingredient):
    """(the ingredients that stand in for `ingredient`, scaled to its quantity; a hint)."""
    swap = SWAPS.get(ingredient.name)
    if swap is None:
        raise RecipeBoxError(f"no substitute known for {ingredient.name}")
    replacements = []
    for name, ratio, unit in swap.parts:
        if ingredient.quantity is None:
            replacements.append(Ingredient(name))
            continue
        symbol = ingredient.quantity.unit if unit is None else unit
        replacements.append(Ingredient(name, Quantity(ingredient.quantity.amount * ratio, symbol)))
    return replacements, swap.hint
