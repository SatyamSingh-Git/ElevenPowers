"""Stage 3: fibre_g is in grams to one decimal, and zero when nothing in the recipe has fibre."""
from recipebox.services.nutrition import nutrition_for
from recipebox.storage.recipe_text import parse_recipe

OATS = """title: Overnight Oats
servings: 1

ingredients:
- 100 g oats
- 1 banana
- 1 tsp vanilla
"""

CUSTARD = """title: Custard
servings: 2

ingredients:
- 500 ml milk
- 3 eggs
- 50 g sugar
"""


def test_fibre_from_weights_and_items():
    summary = nutrition_for(parse_recipe(OATS))
    assert summary.per_serving["fibre_g"] == 13.7
    assert summary.missing == ["vanilla"]


def test_no_fibre_is_zero():
    summary = nutrition_for(parse_recipe(CUSTARD))
    assert summary.per_serving["fibre_g"] == 0.0
