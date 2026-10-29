"""Nutrition per serving, from the food composition tables."""
from dataclasses import dataclass, field

from .. import _generated
from ..core import units

# Summary field -> column of the composition table, in the order summaries list them.
FIELDS = {
    "kcal": "energy_kcal",
    "protein_g": "protein",
    "fat_g": "fat",
    "carbs_g": "carbohydrate",
}

# Used for a volume of something the density table does not list.
DEFAULT_DENSITY = 1.0


@dataclass
class NutritionSummary:
    title: str
    servings: int
    per_serving: dict
    # Ingredients that could not be counted: unknown foods, or counts with no known weight.
    missing: list = field(default_factory=list)


def grams(name, quantity):
    """The weight of `quantity` of `name` in grams, or None when it cannot be known."""
    unit = units.unit(quantity.unit)
    if unit.dimension == units.MASS:
        return float(quantity.amount * unit.factor)
    if unit.dimension == units.VOLUME:
        return float(quantity.amount * unit.factor) * _generated.DENSITY_G_PER_ML.get(name, DEFAULT_DENSITY)
    each = _generated.GRAMS_EACH.get(name)
    return None if each is None else float(quantity.amount) * each


def _rounded(name, value):
    return round(value) if name == "kcal" else round(value, 1)


def totals(recipe):
    """(field totals for the whole recipe, names that could not be counted)."""
    columns = [_generated.NUTRIENT_COLUMNS.index(column) for column in FIELDS.values()]
    sums = dict.fromkeys(FIELDS, 0.0)
    missing = []
    for ingredient in recipe.ingredients:
        if ingredient.quantity is None:
            continue
        row = _generated.NUTRIENTS_PER_100G.get(ingredient.name)
        weight = grams(ingredient.name, ingredient.quantity)
        if row is None or weight is None:
            missing.append(ingredient.name)
            continue
        for name, column in zip(FIELDS, columns):
            sums[name] += row[column] * weight / 100
    return sums, missing


def nutrition_for(recipe):
    """Per-serving nutrition for `recipe` as written."""
    sums, missing = totals(recipe)
    per_serving = {name: _rounded(name, value / recipe.servings) for name, value in sums.items()}
    return NutritionSummary(recipe.title, recipe.servings, per_serving, missing)

