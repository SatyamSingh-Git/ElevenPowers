"""Suggesting a week of meals from the library."""
from ..core.plan import DAYS, MealEntry, Plan
from ..errors import RecipeBoxError


def suggest_plan(library, meals=("dinner",), tag=None, days=DAYS):
    """Fill each meal of each day, taking recipes in id order and starting over when they run out.

    With `tag`, only recipes carrying it are used. The same inputs always give
    the same plan.
    """
    recipes = [recipe for recipe in library if tag is None or tag.lower() in recipe.tags]
    if not recipes:
        raise RecipeBoxError(f"no recipes tagged {tag}" if tag else "the library is empty")
    plan = Plan()
    turn = 0
    for day in days:
        for meal in meals:
            plan.add(MealEntry(day, meal, recipes[turn % len(recipes)]))
            turn += 1
    return plan


def replace_meal(plan, day, meal, recipe, servings=None):
    """A copy of `plan` with `recipe` for that meal, replacing whatever was planned."""
    kept = [entry for entry in plan.entries if (entry.day, entry.meal) != (day, meal)]
    return Plan(kept + [MealEntry(day, meal, recipe, servings)])
