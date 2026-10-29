"""Stage 6: build_shopping_list() puts eggs in the aisle `eggs`."""
from recipebox.core.plan import MealEntry, Plan
from recipebox.services.shopping import build_shopping_list
from recipebox.storage.recipe_text import parse_recipe

OMELETTE = """title: Omelette
servings: 1

ingredients:
- 3 eggs
- 2 tbsp milk
- 10 g butter
- 1 tomato
"""


def test_egg_line_aisle():
    plan = Plan([MealEntry("tuesday", "breakfast", parse_recipe(OMELETTE), servings=2)])
    lines = {line.name: line for line in build_shopping_list(plan)}
    assert lines["egg"].aisle == "eggs"
    assert lines["egg"].quantity.amount == 6
    assert lines["milk"].aisle == "dairy"
    assert lines["butter"].aisle == "dairy"
    assert lines["tomato"].aisle == "produce"
