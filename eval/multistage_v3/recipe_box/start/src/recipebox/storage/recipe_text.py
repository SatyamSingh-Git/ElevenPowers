"""Recipe text files: the hand-written format `recipebox add` reads.

    title: Fluffy Pancakes
    servings: 4
    time: 25 min
    tags: breakfast, sweet

    ingredients:
    - 1 1/2 cup flour
    - 2 eggs

    steps:
    1. Whisk everything together.
"""
from pathlib import Path
import re

from ..core.ingredients import format_ingredient, parse_ingredient
from ..core.recipe import Recipe, normalise_tags, validate
from ..errors import RecipeBoxError, RecipeError

HEADER_FIELDS = ("title", "servings", "time", "tags")
SECTIONS = ("ingredients", "steps")

_TIME = re.compile(r"(?:(\d+)\s*h(?:ours?)?)?\s*(?:(\d+)\s*m(?:in(?:utes?)?)?)?")
_STEP_NUMBER = re.compile(r"^\d+[.)]\s*")


def parse_minutes(text):
    """`25`, `25 min`, `1 h 30 min` or `2 hours` as whole minutes."""
    text = text.strip().lower()
    if text.isdigit():
        return int(text)
    match = _TIME.fullmatch(text)
    if not text or match is None:
        raise RecipeError(f"cannot read time {text}")
    hours, minutes = match.groups()
    return int(hours or 0) * 60 + int(minutes or 0)


def format_minutes(minutes):
    hours, rest = divmod(minutes, 60)
    if hours and rest:
        return f"{hours} h {rest} min"
    return f"{hours} h" if hours else f"{rest} min"


def parse_recipe(text, source="<recipe>"):
    fields, ingredients, steps = {}, [], []
    section = None
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        where = f"{source} line {number}"
        key, colon, value = line.partition(":")
        key = key.strip().lower()
        if colon and not value.strip() and key in SECTIONS:
            section = key
            continue
        if section is None:
            if not colon or key not in HEADER_FIELDS:
                raise RecipeError(f"{where}: unknown field {key}")
            fields[key] = value.strip()
        elif section == "ingredients":
            try:
                ingredients.append(parse_ingredient(line))
            except RecipeBoxError as error:
                raise RecipeError(f"{where}: {error}") from error
        else:
            steps.append(_STEP_NUMBER.sub("", line))
    for required in ("title", "servings"):
        if required not in fields:
            raise RecipeError(f"{source}: missing {required}")
    if not fields["servings"].isdigit():
        raise RecipeError(f"{source}: servings must be a whole number")
    recipe = Recipe(
        title=fields["title"],
        servings=int(fields["servings"]),
        ingredients=tuple(ingredients),
        steps=tuple(steps),
        minutes=parse_minutes(fields["time"]) if "time" in fields else None,
        tags=normalise_tags(fields.get("tags", "").split(",")),
    )
    return validate(recipe)


def parse_recipes(text, source="<recipe>"):
    """Every recipe in `text`; recipes in one file are separated by a line of `---`."""
    chunks, current = [], []
    for line in text.splitlines():
        if line.strip() == "---":
            chunks.append(current)
            current = []
        else:
            current.append(line)
    chunks.append(current)
    return [parse_recipe("\n".join(chunk), source) for chunk in chunks if any(line.strip() for line in chunk)]


def read_recipe_file(path):
    path = Path(path)
    return parse_recipes(path.read_text(encoding="utf-8"), source=path.name)


def dump_recipe(recipe):
    lines = [f"title: {recipe.title}", f"servings: {recipe.servings}"]
    if recipe.minutes is not None:
        lines.append(f"time: {format_minutes(recipe.minutes)}")
    if recipe.tags:
        lines.append(f"tags: {', '.join(recipe.tags)}")
    lines += ["", "ingredients:"]
    lines += [f"- {format_ingredient(ingredient)}" for ingredient in recipe.ingredients]
    if recipe.steps:
        lines += ["", "steps:"]
        lines += [f"{number}. {step}" for number, step in enumerate(recipe.steps, 1)]
    return "\n".join(lines) + "\n"
