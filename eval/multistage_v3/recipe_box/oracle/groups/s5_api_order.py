"""Stage 5: build_shopping_list() returns its lines alphabetically by name."""
from fractions import Fraction

from recipebox.core.pantry import Pantry
from recipebox.core.plan import MealEntry, Plan
from recipebox.core.quantity import Quantity
from recipebox.services.shopping import build_shopping_list
from recipebox.storage.recipe_text import parse_recipe

SALAD = """title: Potato Salad
servings: 2

ingredients:
- 500 g potatoes
- 100 g yogurt
- 1 lemon
- 2 slices bacon
- 1 tsp black pepper
- 2 spring onions
"""

TOAST = """title: Toast
servings: 1

ingredients:
- 2 slices bread
- 10 g butter
- 1 tsp honey
"""


def test_lines_by_name():
    plan = Plan([MealEntry("monday", "lunch", parse_recipe(SALAD)), MealEntry("tuesday", "breakfast", parse_recipe(TOAST))])
    names = [line.name for line in build_shopping_list(plan)]
    assert names == ["bacon", "black pepper", "bread", "butter", "green onion", "honey", "lemon", "potato", "yogurt"]


def test_order_after_the_pantry():
    pantry = Pantry()
    pantry.add("butter", Quantity(Fraction(500), "g"))
    pantry.add("lemon", Quantity(Fraction(6)))
    plan = Plan([MealEntry("monday", "lunch", parse_recipe(SALAD)), MealEntry("tuesday", "breakfast", parse_recipe(TOAST))])
    names = [line.name for line in build_shopping_list(plan, pantry)]
    assert names == ["bacon", "black pepper", "bread", "green onion", "honey", "potato", "yogurt"]
