"""Finding recipes by words in their title, tags and ingredients."""
from dataclasses import dataclass

from ..core.ingredients import canonical_name

TITLE_WEIGHT = 3
TAG_WEIGHT = 2
INGREDIENT_WEIGHT = 1


@dataclass(frozen=True)
class Match:
    recipe: object
    score: int


def _score(recipe, word):
    score = 0
    if word in recipe.title.lower().split():
        score += TITLE_WEIGHT
    if word in recipe.tags:
        score += TAG_WEIGHT
    singular = canonical_name(word)
    if any(singular in ingredient.name.split() or singular == ingredient.name for ingredient in recipe.ingredients):
        score += INGREDIENT_WEIGHT
    return score


def search(library, query="", tag=None, max_minutes=None):
    """Recipes matching every word of `query`, best first, then by title.

    `tag` keeps recipes carrying that tag; `max_minutes` keeps recipes known to
    take no longer than that.
    """
    words = query.lower().split()
    matches = []
    for recipe in library:
        if tag is not None and tag.lower() not in recipe.tags:
            continue
        if max_minutes is not None and (recipe.minutes is None or recipe.minutes > max_minutes):
            continue
        scores = [_score(recipe, word) for word in words]
        if all(scores):
            matches.append(Match(recipe, sum(scores)))
    matches.sort(key=lambda match: (-match.score, match.recipe.title.lower()))
    return matches
