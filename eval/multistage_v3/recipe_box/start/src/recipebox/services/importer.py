"""Importing a bundle exported by another recipebox.

Bundles come from elsewhere, so every field is checked before anything is
added, and a problem is reported with where it is: `recipe 2, ingredient 3: ...`.
"""
from dataclasses import dataclass, field
import json
from pathlib import Path

from ..core import units
from ..core.ingredients import Ingredient, canonical_name
from ..core.quantity import Quantity, parse_amount
from ..core.recipe import Recipe, normalise_tags, validate
from ..errors import BundleError, RecipeBoxError


@dataclass
class ImportReport:
    added: list = field(default_factory=list)
    replaced: list = field(default_factory=list)
    skipped: list = field(default_factory=list)


def _require(entry, key, kind, where):
    if key not in entry:
        raise BundleError(f"{where}: missing {key}")
    value = entry[key]
    if not isinstance(value, kind) or isinstance(value, bool):
        raise BundleError(f"{where}: {key} has the wrong type")
    return value


def _read_ingredient(entry, where):
    if not isinstance(entry, dict):
        raise BundleError(f"{where}: expected an object")
    name = canonical_name(_require(entry, "item", str, where))
    if not name:
        raise BundleError(f"{where}: item is empty")
    raw = entry.get("amount")
    quantity = None
    if raw is not None:
        if not isinstance(raw, str):
            raise BundleError(f"{where}: cannot read amount {raw!r}")
        try:
            amount = parse_amount(raw)
        except RecipeBoxError as error:
            raise BundleError(f"{where}: {error}") from error
        symbol = entry.get("unit", "")
        if not isinstance(symbol, str) or units.lookup(symbol) is None:
            raise BundleError(f"{where}: unknown unit {symbol}")
        quantity = Quantity(amount, units.lookup(symbol).symbol)
    note = entry.get("note", "")
    return Ingredient(name, quantity, note if isinstance(note, str) else "")


def _read_recipe(entry, where):
    if not isinstance(entry, dict):
        raise BundleError(f"{where}: expected an object")
    title = _require(entry, "title", str, where).strip()
    servings = _require(entry, "servings", int, where)
    ingredients = _require(entry, "ingredients", list, where)
    minutes = entry.get("minutes")
    if minutes is not None and (not isinstance(minutes, int) or isinstance(minutes, bool)):
        raise BundleError(f"{where}: minutes has the wrong type")
    recipe = Recipe(
        title=title,
        servings=servings,
        ingredients=tuple(
            _read_ingredient(item, f"{where}, ingredient {number}") for number, item in enumerate(ingredients, 1)
        ),
        steps=tuple(str(step) for step in entry.get("steps", [])),
        minutes=minutes,
        tags=normalise_tags(str(tag) for tag in entry.get("tags", [])),
    )
    try:
        return validate(recipe)
    except RecipeBoxError as error:
        raise BundleError(f"{where}: {error}") from error


def read_bundle(path):
    """Every recipe in the bundle at `path`, checked."""
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BundleError(f"{path.name}: cannot read bundle: {error}") from error
    if not isinstance(data, dict) or data.get("recipebox") != 1 or not isinstance(data.get("recipes"), list):
        raise BundleError(f"{path.name}: not a recipebox bundle")
    return [_read_recipe(entry, f"recipe {number}") for number, entry in enumerate(data["recipes"], 1)]


def import_bundle(library, path, replace=False):
    """Add a bundle's recipes; one the library already has is skipped unless `replace`."""
    report = ImportReport()
    for recipe in read_bundle(path):
        if recipe.id in library:
            if not replace:
                report.skipped.append(recipe.id)
                continue
            report.replaced.append(recipe.id)
        else:
            report.added.append(recipe.id)
        library.add(recipe, replace=True)
    return report
