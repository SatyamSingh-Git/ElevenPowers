"""Scaling a recipe to a different number of servings."""
from fractions import Fraction
import math

from ..core import units
from ..core.ingredients import Ingredient
from ..core.quantity import Quantity
from ..core.recipe import MAX_SERVINGS, check_servings
from ..errors import RecipeError

# Counted things (eggs, cloves, cans) are rounded up to the nearest half.
COUNT_STEP = Fraction(1, 2)


def scale_quantity(quantity, factor):
    amount = quantity.amount * factor
    if units.unit(quantity.unit).dimension == units.COUNT:
        amount = math.ceil(amount / COUNT_STEP) * COUNT_STEP
    return Quantity(amount, quantity.unit)


def scale_recipe(recipe, servings):
    """`recipe` for `servings` people; ingredients without an amount stay as they are."""
    check_servings(servings)
    if servings == recipe.servings:
        return recipe
    factor = Fraction(servings, recipe.servings)
    scaled = [
        Ingredient(ingredient.name, scale_quantity(ingredient.quantity, factor), ingredient.note)
        if ingredient.quantity is not None else ingredient
        for ingredient in recipe.ingredients
    ]
    return recipe.with_ingredients(scaled, servings)


def servings_for(recipe, name, quantity):
    """The most servings that `quantity` of ingredient `name` is enough for, between 1 and the limit."""
    for ingredient in recipe.ingredients:
        if ingredient.name != name or ingredient.quantity is None:
            continue
        if not units.convertible(ingredient.quantity.unit, quantity.unit):
            raise RecipeError(f"{recipe.title} measures {name} in {ingredient.quantity.unit or 'items'}")
        needed = units.convert(ingredient.quantity.amount, ingredient.quantity.unit, quantity.unit)
        servings = math.floor(quantity.amount * recipe.servings / needed)
        return min(max(servings, 1), MAX_SERVINGS)
    raise RecipeError(f"{recipe.title} has no measured {name}")
