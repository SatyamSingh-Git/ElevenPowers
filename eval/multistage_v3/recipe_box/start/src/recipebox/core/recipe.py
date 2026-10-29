"""The recipe model, its id and its limits."""
from dataclasses import dataclass, field, replace

from ..errors import RecipeError

MIN_SERVINGS = 1
MAX_SERVINGS = 100
MAX_TITLE = 80
MAX_TAGS = 10
MAX_MINUTES = 24 * 60


def recipe_id(title):
    """The id a recipe is known by in the library and on the command line."""
    return "-".join(title.lower().split())


@dataclass(frozen=True)
class Recipe:
    title: str
    servings: int
    ingredients: tuple = ()
    steps: tuple = ()
    minutes: int | None = None
    tags: tuple = field(default=())

    @property
    def id(self):
        return recipe_id(self.title)

    def with_ingredients(self, ingredients, servings):
        return replace(self, ingredients=tuple(ingredients), servings=servings)


def check_servings(servings):
    if not MIN_SERVINGS <= servings <= MAX_SERVINGS:
        raise RecipeError(f"servings must be between {MIN_SERVINGS} and {MAX_SERVINGS}")


def validate(recipe):
    """Raise RecipeError for the first limit `recipe` breaks."""
    if not recipe.title.strip():
        raise RecipeError("a recipe needs a title")
    if len(recipe.title) > MAX_TITLE:
        raise RecipeError(f"title is longer than {MAX_TITLE} characters")
    check_servings(recipe.servings)
    if not recipe.ingredients:
        raise RecipeError(f"{recipe.title} has no ingredients")
    if recipe.minutes is not None and not 0 < recipe.minutes <= MAX_MINUTES:
        raise RecipeError(f"time must be between 1 and {MAX_MINUTES} minutes")
    if len(recipe.tags) > MAX_TAGS:
        raise RecipeError(f"a recipe has at most {MAX_TAGS} tags")
    return recipe


def normalise_tags(tags):
    """Lower-case, without blanks or repeats, in the order given."""
    seen = []
    for tag in tags:
        tag = tag.strip().lower()
        if tag and tag not in seen:
            seen.append(tag)
    return tuple(seen)
