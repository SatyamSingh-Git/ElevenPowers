"""A week's meal plan: which recipe is cooked for which meal, and for how many."""
from dataclasses import dataclass

from .recipe import check_servings

DAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
MEALS = ("breakfast", "lunch", "dinner", "snack")


@dataclass(frozen=True)
class MealEntry:
    day: str
    meal: str
    recipe: object
    # None cooks the recipe as written.
    servings: int | None = None

    def __post_init__(self):
        if self.servings is not None:
            check_servings(self.servings)

    @property
    def portions(self):
        return self.servings or self.recipe.servings


class Plan:
    def __init__(self, entries=()):
        self.entries = list(entries)

    def add(self, entry):
        self.entries.append(entry)

    def on(self, day):
        """The day's entries, breakfast first."""
        return sorted((e for e in self.entries if e.day == day), key=lambda e: MEALS.index(e.meal))

    def days(self):
        """Days that have at least one meal, Monday first."""
        return [day for day in DAYS if any(e.day == day for e in self.entries)]

    def recipes(self):
        """Each planned recipe once, in plan order."""
        seen = {}
        for entry in self.entries:
            seen.setdefault(entry.recipe.title, entry.recipe)
        return list(seen.values())

    def __len__(self):
        return len(self.entries)
