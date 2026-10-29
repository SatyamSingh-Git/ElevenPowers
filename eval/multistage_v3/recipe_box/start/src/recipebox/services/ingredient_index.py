"""Which recipes use which ingredients."""
from ..core.catalog import aisle_for
from ..core.ingredients import canonical_name


def ingredient_index(library):
    """{ingredient name: titles of the recipes using it}, names and titles sorted."""
    index = {}
    for recipe in library:
        for ingredient in recipe.ingredients:
            titles = index.setdefault(ingredient.name, [])
            if recipe.title not in titles:
                titles.append(recipe.title)
    return {name: sorted(index[name], key=str.lower) for name in sorted(index)}


def recipes_using(library, name):
    """Recipes with `name` among their ingredients, by title."""
    wanted = canonical_name(name)
    found = [recipe for recipe in library if any(ingredient.name == wanted for ingredient in recipe.ingredients)]
    return sorted(found, key=lambda recipe: recipe.title.lower())


def ingredients_by_aisle(library):
    """{aisle code: ingredient names}, for aisles the library uses."""
    grouped = {}
    for name in ingredient_index(library):
        grouped.setdefault(aisle_for(name), []).append(name)
    return grouped
