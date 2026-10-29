from fractions import Fraction

from recipebox.core.pantry import Pantry
from recipebox.core.plan import MealEntry, Plan
from recipebox.core.quantity import Quantity
from recipebox.services.shopping import build_shopping_list


def _lines(plan, pantry=None):
    return {line.name: line for line in build_shopping_list(plan, pantry)}


def test_adds_up_across_meals(pancakes, soup):
    plan = Plan([
        MealEntry("monday", "breakfast", pancakes),
        MealEntry("tuesday", "breakfast", pancakes, servings=2),
        MealEntry("tuesday", "lunch", soup),
    ])
    lines = _lines(plan)
    assert lines["flour"].quantity == Quantity(Fraction(9, 4), "cup")
    assert lines["egg"].quantity == Quantity(Fraction(3), "")
    assert lines["garlic"].quantity == Quantity(Fraction(2), "clove")
    assert lines["flour"].recipes == ["Fluffy Pancakes"]
    assert lines["salt"].quantity is None


def test_mixed_units_add_up_in_the_base_unit(pancakes, soup):
    plan = Plan([MealEntry("monday", "lunch", soup), MealEntry("monday", "dinner", soup, servings=6)])
    lines = _lines(plan)
    assert lines["vegetable stock"].quantity == Quantity(Fraction(2), "l")
    assert lines["olive oil"].quantity == Quantity(Fraction(8), "tbsp")


def test_large_amounts_are_shown_in_kg_and_l(soup):
    lines = _lines(Plan([MealEntry("monday", "lunch", soup, servings=8)]))
    assert lines["vegetable stock"].quantity == Quantity(Fraction(2), "l")


def test_pantry_is_used_first(pancakes):
    pantry = Pantry()
    pantry.add("milk", Quantity(Fraction(1, 2), "cup"))
    pantry.add("egg", Quantity(Fraction(6), ""))
    pantry.add("salt")
    lines = _lines(Plan([MealEntry("monday", "breakfast", pancakes)]), pantry)
    assert lines["milk"].quantity == Quantity(Fraction(3, 4), "cup")
    assert "egg" not in lines
    assert "salt" not in lines


def test_pantry_in_other_units_is_converted(pancakes):
    pantry = Pantry()
    pantry.add("butter", Quantity(Fraction(1, 100), "kg"))
    lines = _lines(Plan([MealEntry("monday", "breakfast", pancakes)]), pantry)
    assert lines["butter"].quantity == Quantity(Fraction(20), "g")


def test_aisles(pancakes, soup):
    lines = _lines(Plan([MealEntry("monday", "breakfast", pancakes), MealEntry("monday", "lunch", soup)]))
    assert lines["tomato"].aisle == "produce"
    assert lines["milk"].aisle == "dairy"
    assert lines["flour"].aisle == "pantry"


def test_order_is_by_aisle_then_name(pancakes, soup):
    plan = Plan([MealEntry("monday", "breakfast", pancakes), MealEntry("monday", "lunch", soup)])
    names = [line.name for line in build_shopping_list(plan)]
    assert names == [
        "garlic", "onion", "tomato",
        "butter", "egg", "milk",
        "flour", "olive oil", "salt", "sugar", "vegetable stock",
    ]
