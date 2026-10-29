"""Meal plan files, written by hand or by `plan suggest`.

One meal per line, naming the recipe by its title and optionally how many it
is cooked for:

    monday dinner: Mac & Cheese x6
    tuesday lunch: Tomato Soup

Blank lines and lines starting with # are ignored.
"""
from pathlib import Path
import re

from ..core.plan import DAYS, MEALS, MealEntry, Plan
from ..errors import PlanError, RecipeBoxError

_LINE = re.compile(r"(\w+)\s+(\w+)\s*:\s*(.+?)(?:\s+x(\d+))?")


def _title_key(title):
    # Plan files name recipes by title, while the library keys them by id: the title
    # lower-cased with its words joined by dashes.
    return "-".join(title.lower().split())


def parse_plan(text, library):
    plan = Plan()
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = _LINE.fullmatch(line)
        if match is None:
            raise PlanError(f'plan line {number}: expected "<day> <meal>: <title>"')
        day, meal, title, servings = match.groups()
        day, meal = day.lower(), meal.lower()
        if day not in DAYS:
            raise PlanError(f"plan line {number}: unknown day {day}")
        if meal not in MEALS:
            raise PlanError(f"plan line {number}: unknown meal {meal}")
        recipe = library.find(_title_key(title))
        if recipe is None:
            raise PlanError(f"plan line {number}: no recipe titled {title}")
        try:
            plan.add(MealEntry(day, meal, recipe, int(servings) if servings else None))
        except RecipeBoxError as error:
            raise PlanError(f"plan line {number}: {error}") from error
    return plan


def load_plan(path, library):
    path = Path(path)
    if not path.is_file():
        raise PlanError(f"no plan file at {path}")
    return parse_plan(path.read_text(encoding="utf-8"), library)


def format_plan(plan):
    lines = []
    for day in plan.days():
        for entry in plan.on(day):
            line = f"{entry.day} {entry.meal}: {entry.recipe.title}"
            if entry.servings is not None:
                line += f" x{entry.servings}"
            lines.append(line)
    return "\n".join(lines) + "\n" if lines else ""


def save_plan(plan, path):
    Path(path).write_text(format_plan(plan), encoding="utf-8")
