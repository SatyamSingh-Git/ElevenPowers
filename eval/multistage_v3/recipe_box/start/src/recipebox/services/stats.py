"""Library statistics for `recipebox stats`."""
from collections import Counter
from dataclasses import dataclass


@dataclass
class LibraryStats:
    recipes: int
    timed: int
    # Whole minutes, or None when no recipe gives a time.
    average_minutes: int | None
    quickest: object
    common_ingredients: list
    common_tags: list


def library_stats(library, top=5):
    """Counts over the whole library; ties in the top lists go to the name first in the alphabet."""
    recipes = list(library)
    timed = [recipe for recipe in recipes if recipe.minutes is not None]
    ingredients = Counter(ingredient.name for recipe in recipes for ingredient in recipe.ingredients)
    tags = Counter(tag for recipe in recipes for tag in recipe.tags)

    def ranked(counter):
        return sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:top]

    return LibraryStats(
        recipes=len(recipes),
        timed=len(timed),
        average_minutes=round(sum(recipe.minutes for recipe in timed) / len(timed)) if timed else None,
        quickest=min(timed, key=lambda recipe: (recipe.minutes, recipe.title)) if timed else None,
        common_ingredients=ranked(ingredients),
        common_tags=ranked(tags),
    )

