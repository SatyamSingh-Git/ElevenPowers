"""Markdown versions of the recipe card and the shopping list, for notes apps and chat."""
from ..core.ingredients import describe_ingredient
from ..core.quantity import display_quantity
from ..storage.recipe_text import format_minutes


def recipe_markdown(recipe):
    out = [f"# {recipe.title}", ""]
    facts = [f"**Serves** {recipe.servings}"]
    if recipe.minutes is not None:
        facts.append(f"**Time** {format_minutes(recipe.minutes)}")
    if recipe.tags:
        facts.append("**Tags** " + ", ".join(recipe.tags))
    out += [" · ".join(facts), "", "## Ingredients", ""]
    out += [f"- {describe_ingredient(ingredient)}" for ingredient in recipe.ingredients]
    if recipe.steps:
        out += ["", "## Method", ""]
        out += [f"{number}. {step}" for number, step in enumerate(recipe.steps, 1)]
    return "\n".join(out) + "\n"


def shopping_markdown(lines):
    """A checklist, one box per line, in the order given."""
    if not lines:
        return "Nothing to buy.\n"
    out = []
    for line in lines:
        amount = "" if line.quantity is None else f" — {display_quantity(line.quantity)}"
        out.append(f"- [ ] {line.name}{amount}")
    return "\n".join(out) + "\n"
