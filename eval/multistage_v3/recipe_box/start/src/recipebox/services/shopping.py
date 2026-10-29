"""Shopping lists: what a meal plan needs, added up across recipes, less what the pantry holds."""
from dataclasses import dataclass, field

from ..core import units
from ..core.catalog import AISLE_ORDER, aisle_for
from ..core.quantity import Quantity
from .scaling import scale_recipe

# At this many g or ml a line is shown in kg or l.
METRIC_UPGRADE = 1000
UPGRADES = {"g": "kg", "ml": "l"}


@dataclass
class ShoppingLine:
    name: str
    # None when no recipe gave an amount ("salt, to taste").
    quantity: Quantity | None
    aisle: str
    recipes: list = field(default_factory=list)


def _group(quantity):
    """Quantities in one group add up: all masses, all volumes, or one count unit."""
    if quantity is None:
        return None
    unit = units.unit(quantity.unit)
    return unit.symbol if unit.dimension == units.COUNT else unit.dimension


def _total(quantities):
    symbols = {quantity.unit for quantity in quantities}
    if len(symbols) == 1:
        return Quantity(sum(quantity.amount for quantity in quantities), symbols.pop())
    base = units.BASE[units.unit(quantities[0].unit).dimension]
    return Quantity(sum(quantity.to(base).amount for quantity in quantities), base)


def _needed(plan):
    """{(name, group): (quantities, recipe titles)} for every planned meal."""
    needed = {}
    for entry in plan.entries:
        recipe = entry.recipe if entry.servings is None else scale_recipe(entry.recipe, entry.servings)
        for ingredient in recipe.ingredients:
            quantities, titles = needed.setdefault((ingredient.name, _group(ingredient.quantity)), ([], []))
            if ingredient.quantity is not None:
                quantities.append(ingredient.quantity)
            if recipe.title not in titles:
                titles.append(recipe.title)
    return needed


def _merge(needed):
    lines = {}
    for (name, group), (quantities, titles) in needed.items():
        quantity = _total(quantities) if quantities else None
        lines[(name, group)] = ShoppingLine(name, quantity, aisle_for(name), list(titles))
    # An amount elsewhere covers a line that has none.
    for name, group in list(lines):
        if group is None and any(other == name and g is not None for other, g in lines):
            del lines[(name, group)]
    return list(lines.values())


def _after_pantry(line, pantry):
    """What is still to buy once the pantry is used; None when nothing is."""
    held = pantry.get(line.name)
    if held is None:
        return line
    if held.staple or line.quantity is None:
        return None
    if not units.convertible(held.quantity.unit, line.quantity.unit):
        return line
    left = line.quantity.amount - units.convert(held.quantity.amount, held.quantity.unit, line.quantity.unit)
    if left <= 0:
        return None
    return ShoppingLine(line.name, Quantity(left, line.quantity.unit), line.aisle, line.recipes)


def _upgrade(line):
    quantity = line.quantity
    if quantity is None or quantity.unit not in UPGRADES or quantity.amount < METRIC_UPGRADE:
        return line
    return ShoppingLine(line.name, quantity.to(UPGRADES[quantity.unit]), line.aisle, line.recipes)


def build_shopping_list(plan, pantry=None):
    """Lines to buy for `plan`, in aisle order and by name within an aisle."""
    lines = _merge(_needed(plan))
    if pantry is not None:
        lines = [kept for kept in (_after_pantry(line, pantry) for line in lines) if kept is not None]
    lines = [_upgrade(line) for line in lines]
    lines.sort(key=lambda line: (AISLE_ORDER.index(line.aisle), line.name))
    return lines
