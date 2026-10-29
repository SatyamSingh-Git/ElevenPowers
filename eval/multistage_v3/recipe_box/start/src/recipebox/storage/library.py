"""The recipe library, kept in `library.json` in the recipebox home."""
import json
from pathlib import Path

from ..core.ingredients import Ingredient
from ..core.quantity import Quantity, format_amount, parse_amount
from ..core.recipe import Recipe
from ..errors import DuplicateRecipe, RecipeBoxError, RecipeNotFound

LIBRARY_VERSION = 1


def _ingredient_to_dict(ingredient):
    quantity = ingredient.quantity
    return {
        "item": ingredient.name,
        "amount": None if quantity is None else format_amount(quantity.amount),
        "unit": "" if quantity is None else quantity.unit,
        "note": ingredient.note,
    }


def _ingredient_from_dict(data):
    quantity = None
    if data["amount"] is not None:
        quantity = Quantity(parse_amount(data["amount"]), data["unit"])
    return Ingredient(data["item"], quantity, data.get("note", ""))


def recipe_to_dict(recipe):
    return {
        "title": recipe.title,
        "servings": recipe.servings,
        "minutes": recipe.minutes,
        "tags": list(recipe.tags),
        "ingredients": [_ingredient_to_dict(ingredient) for ingredient in recipe.ingredients],
        "steps": list(recipe.steps),
    }


def recipe_from_dict(data):
    return Recipe(
        title=data["title"],
        servings=data["servings"],
        ingredients=tuple(_ingredient_from_dict(entry) for entry in data["ingredients"]),
        steps=tuple(data.get("steps", ())),
        minutes=data.get("minutes"),
        tags=tuple(data.get("tags", ())),
    )


class Library:
    def __init__(self, path, recipes=()):
        self.path = Path(path)
        self._recipes = {}
        for recipe in recipes:
            self.add(recipe)

    @classmethod
    def load(cls, path):
        """The library at `path`; a missing file is an empty library."""
        path = Path(path)
        if not path.is_file():
            return cls(path)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise RecipeBoxError(f"{path.name} is not valid JSON: {error}") from error
        if data.get("version") != LIBRARY_VERSION:
            raise RecipeBoxError(f"{path.name} has version {data.get('version')}, expected {LIBRARY_VERSION}")
        return cls(path, (recipe_from_dict(entry) for entry in data["recipes"]))

    def save(self):
        """Write the library, keeping the previous file as `library.json.bak`."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.is_file():
            self.path.replace(self.path.with_name(self.path.name + ".bak"))
        data = {"version": LIBRARY_VERSION, "recipes": [recipe_to_dict(recipe) for recipe in self]}
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def add(self, recipe, replace=False):
        if recipe.id in self._recipes and not replace:
            raise DuplicateRecipe(recipe.id)
        self._recipes[recipe.id] = recipe

    def remove(self, rid):
        if rid not in self._recipes:
            raise RecipeNotFound(rid)
        del self._recipes[rid]

    def find(self, rid):
        return self._recipes.get(rid)

    def get(self, rid):
        recipe = self._recipes.get(rid)
        if recipe is None:
            raise RecipeNotFound(rid)
        return recipe

    def __contains__(self, rid):
        return rid in self._recipes

    def __iter__(self):
        """Recipes in id order."""
        return iter([self._recipes[rid] for rid in sorted(self._recipes)])

    def __len__(self):
        return len(self._recipes)
