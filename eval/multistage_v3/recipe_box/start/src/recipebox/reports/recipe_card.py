"""A recipe as `recipebox show` prints it, and the one-line listings."""
from ..core.ingredients import describe_ingredient
from ..storage.recipe_text import format_minutes


def render_recipe(recipe):
    facts = [f"Serves {recipe.servings}"]
    if recipe.minutes is not None:
        facts.append(format_minutes(recipe.minutes))
    if recipe.tags:
        facts.append(", ".join(recipe.tags))
    out = [recipe.title, " - ".join(facts), "", "Ingredients"]
    out += [f"  {describe_ingredient(ingredient)}" for ingredient in recipe.ingredients]
    if recipe.steps:
        out += ["", "Method"]
        out += [f"  {number}. {step}" for number, step in enumerate(recipe.steps, 1)]
    return "\n".join(out) + "\n"


def render_listing(recipes):
    """`<id>  <title>` per recipe, ids lined up."""
    recipes = list(recipes)
    if not recipes:
        return ""
    width = max(len(recipe.id) for recipe in recipes) + 2
    return "".join(f"{recipe.id.ljust(width)}{recipe.title}\n" for recipe in recipes)
