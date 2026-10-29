from fractions import Fraction
import json

import pytest

from recipebox.core.pantry import Pantry
from recipebox.core.quantity import Quantity
from recipebox.errors import DuplicateRecipe, PantryError, PlanError, RecipeNotFound
from recipebox.storage.library import Library
from recipebox.storage.pantry_file import load_pantry, read_purchases, save_pantry
from recipebox.storage.plan_file import format_plan, parse_plan


def test_library_round_trip(tmp_path, pancakes, soup):
    library = Library(tmp_path / "library.json", [pancakes, soup])
    library.save()
    loaded = Library.load(tmp_path / "library.json")
    assert [recipe.id for recipe in loaded] == ["fluffy-pancakes", "tomato-soup"]
    assert loaded.get("fluffy-pancakes") == pancakes


def test_library_file_fields(tmp_path, pancakes):
    Library(tmp_path / "library.json", [pancakes]).save()
    data = json.loads((tmp_path / "library.json").read_text(encoding="utf-8"))
    assert data["version"] == 1
    flour = data["recipes"][0]["ingredients"][0]
    assert flour == {"item": "flour", "amount": "1 1/2", "unit": "cup", "note": ""}


def test_library_keeps_a_backup(tmp_path, pancakes, soup):
    library = Library(tmp_path / "library.json", [pancakes])
    library.save()
    library.add(soup)
    library.save()
    backup = json.loads((tmp_path / "library.json.bak").read_text(encoding="utf-8"))
    assert len(backup["recipes"]) == 1


def test_library_errors(tmp_path, pancakes):
    library = Library(tmp_path / "library.json", [pancakes])
    with pytest.raises(DuplicateRecipe, match="recipe fluffy-pancakes already exists"):
        library.add(pancakes)
    with pytest.raises(RecipeNotFound, match="no recipe with id waffles"):
        library.get("waffles")


def test_pantry_file_round_trip(tmp_path):
    pantry = Pantry()
    pantry.add("flour", Quantity(Fraction(1, 2), "kg"))
    pantry.add("salt")
    save_pantry(pantry, tmp_path / "pantry.csv")
    assert (tmp_path / "pantry.csv").read_text(encoding="utf-8") == "item,amount,unit\nflour,1/2,kg\nsalt,,\n"
    loaded = load_pantry(tmp_path / "pantry.csv")
    assert loaded.get("flour").quantity == Quantity(Fraction(1, 2), "kg")
    assert loaded.get("salt").staple


def test_pantry_file_header_is_checked(tmp_path):
    (tmp_path / "pantry.csv").write_text("name,qty\nflour,1\n", encoding="utf-8")
    with pytest.raises(PantryError, match="expected the header item,amount,unit"):
        load_pantry(tmp_path / "pantry.csv")


def test_read_purchases(tmp_path):
    (tmp_path / "bought.csv").write_text("item,quantity,unit\nmilk,1 1/2,cup\negg,6,\nsalt,,\n", encoding="utf-8")
    assert read_purchases(tmp_path / "bought.csv") == [
        ("milk", Quantity(Fraction(3, 2), "cup")),
        ("egg", Quantity(Fraction(6), "")),
        ("salt", None),
    ]


def test_parse_plan(tmp_path, pancakes, soup):
    library = Library(tmp_path / "library.json", [pancakes, soup])
    plan = parse_plan("# week\nmonday breakfast: Fluffy Pancakes\n\nTuesday lunch: tomato soup x4\n", library)
    assert [(e.day, e.meal, e.recipe.title, e.servings) for e in plan.entries] == [
        ("monday", "breakfast", "Fluffy Pancakes", None),
        ("tuesday", "lunch", "Tomato Soup", 4),
    ]
    assert format_plan(plan) == "monday breakfast: Fluffy Pancakes\ntuesday lunch: Tomato Soup x4\n"


@pytest.mark.parametrize("line, message", [
    ("monday pancakes", 'plan line 1: expected "<day> <meal>: <title>"'),
    ("someday dinner: Tomato Soup", "plan line 1: unknown day someday"),
    ("monday brunch: Tomato Soup", "plan line 1: unknown meal brunch"),
    ("monday dinner: Waffles", "plan line 1: no recipe titled Waffles"),
    ("monday dinner: Tomato Soup x500", "plan line 1: servings must be between 1 and 100"),
])
def test_plan_errors(tmp_path, soup, line, message):
    with pytest.raises(PlanError, match=message):
        parse_plan(line, Library(tmp_path / "library.json", [soup]))
