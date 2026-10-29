"""Stage 3: nutrition_for() reports fibre_g after carbs_g."""
from recipebox.services.nutrition import nutrition_for
from recipebox.storage.recipe_text import parse_recipe

PANCAKES = """title: Fluffy Pancakes
servings: 4

ingredients:
- 1 1/2 cup flour
- 2 tbsp sugar
- 2 eggs
- 1 1/4 cup milk
- 30 g butter
"""


def test_fields_in_order():
    summary = nutrition_for(parse_recipe(PANCAKES))
    assert list(summary.per_serving) == ["kcal", "protein_g", "fat_g", "carbs_g", "fibre_g"]


def test_fibre_per_serving():
    summary = nutrition_for(parse_recipe(PANCAKES))
    # Only the flour has fibre: 1 1/2 cup at 0.53 g/ml is about 188 g, at 2.7 g per 100 g, over 4 servings.
    assert summary.per_serving["fibre_g"] == 1.3
    assert summary.per_serving["kcal"] == 331
    assert summary.per_serving["carbs_g"] == 46.0
