from fractions import Fraction
import json

import pytest

from recipebox.core.ingredients import Ingredient
from recipebox.core.pantry import Pantry
from recipebox.core.plan import MealEntry, Plan
from recipebox.core.quantity import Quantity
from recipebox.core.recipe import Recipe
from recipebox.errors import BundleError, PantryError, RecipeError, UnitError
from recipebox.services.conversion import convert_ingredient
from recipebox.services.cookable import cookable
from recipebox.services.importer import import_bundle, read_bundle
from recipebox.services.nutrition import nutrition_for
from recipebox.services.plan_check import check_plan
from recipebox.services.planner import suggest_plan
from recipebox.services.scaling import scale_recipe, servings_for
from recipebox.services.search import search
from recipebox.services.substitutes import substitute
from recipebox.services.weekly import daily_average, week_intake
from recipebox.storage.library import Library


def test_scale_recipe(pancakes):
    half = scale_recipe(pancakes, 2)
    assert half.servings == 2
    assert half.ingredients[0].quantity == Quantity(Fraction(3, 4), "cup")
    assert half.ingredients[5].quantity is None


def test_counts_round_up_to_halves(pancakes):
    assert scale_recipe(pancakes, 3).ingredients[2].quantity == Quantity(Fraction(3, 2), "")
    assert scale_recipe(pancakes, 1).ingredients[2].quantity == Quantity(Fraction(1, 2), "")


def test_scale_limits(pancakes):
    with pytest.raises(RecipeError, match="servings must be between 1 and 100"):
        scale_recipe(pancakes, 101)


def test_servings_for(pancakes):
    assert servings_for(pancakes, "milk", Quantity(Fraction(5, 2), "cup")) == 8
    with pytest.raises(RecipeError, match="has no measured salt"):
        servings_for(pancakes, "salt", Quantity(Fraction(1), "g"))


def test_nutrition_per_serving():
    recipe = Recipe("Sweet Milk", 2, (
        Ingredient("milk", Quantity(Fraction(200), "g")),
        Ingredient("sugar", Quantity(Fraction(50), "g")),
        Ingredient("vanilla", Quantity(Fraction(1), "tsp")),
    ))
    summary = nutrition_for(recipe)
    assert list(summary.per_serving) == ["kcal", "protein_g", "fat_g", "carbs_g"]
    assert summary.per_serving == {"kcal": 158, "protein_g": 3.2, "fat_g": 3.3, "carbs_g": 29.8}
    assert summary.missing == ["vanilla"]


def test_nutrition_uses_density_and_item_weights():
    recipe = Recipe("Eggy Flour", 1, (
        Ingredient("flour", Quantity(Fraction(100), "ml")),
        Ingredient("egg", Quantity(Fraction(2), "")),
    ))
    assert nutrition_for(recipe).per_serving["kcal"] == round(364 * 0.53 + 143)


def test_week_intake(pancakes, soup):
    plan = Plan([MealEntry("monday", "breakfast", pancakes), MealEntry("monday", "lunch", soup),
                 MealEntry("wednesday", "lunch", soup)])
    week = week_intake(plan)
    assert [day.day for day in week] == ["monday", "wednesday"]
    assert week[0].meals == 2
    average = daily_average(week)
    assert average["kcal"] == pytest.approx((week[0].amounts["kcal"] + week[1].amounts["kcal"]) / 2)


def test_pantry_add_and_use():
    pantry = Pantry()
    pantry.add("Eggs", Quantity(Fraction(6), ""))
    pantry.add("egg", Quantity(Fraction(2), ""))
    assert pantry.get("eggs").quantity == Quantity(Fraction(8), "")
    pantry.use("egg", Quantity(Fraction(8), ""))
    assert "egg" not in pantry
    with pytest.raises(PantryError, match="egg is not in the pantry"):
        pantry.use("egg", Quantity(Fraction(1), ""))


def test_pantry_staples_stay():
    pantry = Pantry()
    pantry.add("salt")
    pantry.add("salt", Quantity(Fraction(1), "kg"))
    pantry.use("salt", Quantity(Fraction(5), "g"))
    assert pantry.get("salt").staple


def test_pantry_rejects_unrelated_units():
    pantry = Pantry()
    pantry.add("flour", Quantity(Fraction(1), "kg"))
    with pytest.raises(PantryError, match="flour: cannot convert cup to kg"):
        pantry.add("flour", Quantity(Fraction(1), "cup"))


def test_search(tmp_path, pancakes, soup):
    library = Library(tmp_path / "library.json", [pancakes, soup])
    assert [m.recipe.title for m in search(library, "tomato")] == ["Tomato Soup"]
    assert [m.recipe.title for m in search(library, "eggs")] == ["Fluffy Pancakes"]
    assert [m.recipe.title for m in search(library, "", max_minutes=30)] == ["Fluffy Pancakes"]
    assert [m.recipe.title for m in search(library, "", tag="lunch")] == ["Tomato Soup"]


def test_suggest_plan_is_round_robin(tmp_path, pancakes, soup):
    plan = suggest_plan(Library(tmp_path / "library.json", [pancakes, soup]), meals=("lunch", "dinner"))
    assert len(plan) == 14
    assert [entry.recipe.title for entry in plan.on("monday")] == ["Fluffy Pancakes", "Tomato Soup"]


def test_check_plan(pancakes, soup):
    plan = Plan([MealEntry("monday", "lunch", soup), MealEntry("tuesday", "lunch", soup),
                 MealEntry("thursday", "breakfast", pancakes)])
    assert [(w.day, w.message) for w in check_plan(plan)] == [
        ("tuesday", "Tomato Soup again, as the day before"),
        ("wednesday", "nothing planned"),
    ]


def test_cookable(tmp_path, pancakes, soup):
    pantry = Pantry()
    for name in ["tomato", "onion", "garlic", "olive oil", "vegetable stock"]:
        pantry.add(name)
    found = cookable(Library(tmp_path / "library.json", [pancakes, soup]), pantry)
    assert [entry.recipe.title for entry in found] == ["Tomato Soup"]


def test_convert_ingredient():
    flour = convert_ingredient("flour", Quantity(Fraction(1), "cup"), "g")
    assert flour.unit == "g" and round(flour.amount) == 125
    assert convert_ingredient("egg", Quantity(Fraction(100), "g"), "") == Quantity(Fraction(2), "")
    with pytest.raises(UnitError, match="the density of tomato is not known"):
        convert_ingredient("tomato", Quantity(Fraction(1), "cup"), "g")


def test_substitute():
    replacements, hint = substitute(Ingredient("buttermilk", Quantity(Fraction(1), "cup")))
    assert replacements == [Ingredient("milk", Quantity(Fraction(1), "cup")),
                            Ingredient("lemon juice", Quantity(Fraction(1, 16), "cup"))]
    assert hint


def _bundle(path, recipes):
    path.write_text(json.dumps({"recipebox": 1, "recipes": recipes}), encoding="utf-8")
    return path


GOOD = {"title": "Toast", "servings": 1, "ingredients": [{"item": "bread", "amount": "2", "unit": "slice"}]}


def test_import_bundle(tmp_path):
    library = Library(tmp_path / "library.json")
    report = import_bundle(library, _bundle(tmp_path / "b.json", [GOOD]))
    assert report.added == ["toast"]
    assert library.get("toast").ingredients[0].quantity == Quantity(Fraction(2), "slice")
    again = import_bundle(library, tmp_path / "b.json")
    assert again.skipped == ["toast"]


@pytest.mark.parametrize("change, message", [
    ({"servings": "1"}, "recipe 1: servings has the wrong type"),
    ({"ingredients": [{"item": "bread", "amount": "lots"}]}, "recipe 1, ingredient 1: cannot read amount lots"),
    ({"ingredients": [{"item": "bread", "amount": "2", "unit": "loaf"}]}, "recipe 1, ingredient 1: unknown unit loaf"),
    ({"servings": 0}, "recipe 1: servings must be between 1 and 100"),
])
def test_import_errors(tmp_path, change, message):
    with pytest.raises(BundleError, match=message):
        read_bundle(_bundle(tmp_path / "b.json", [{**GOOD, **change}]))


def test_not_a_bundle(tmp_path):
    (tmp_path / "b.json").write_text("{}", encoding="utf-8")
    with pytest.raises(BundleError, match="not a recipebox bundle"):
        read_bundle(tmp_path / "b.json")
