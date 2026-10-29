from fractions import Fraction

from recipebox.core.plan import MealEntry, Plan
from recipebox.core.quantity import Quantity
from recipebox.reports.markdown import shopping_markdown
from recipebox.reports.nutrition_report import render_nutrition
from recipebox.reports.plan_report import render_plan
from recipebox.reports.recipe_card import render_recipe
from recipebox.reports.shopping_csv import write_shopping_csv
from recipebox.reports.shopping_text import render_shopping_list
from recipebox.services.nutrition import NutritionSummary
from recipebox.services.shopping import ShoppingLine

LINES = [
    ShoppingLine("onion", Quantity(Fraction(2), ""), "produce"),
    ShoppingLine("milk", Quantity(Fraction(5, 4), "cup"), "dairy"),
    ShoppingLine("flour", Quantity(Fraction(1, 2), "kg"), "pantry"),
    ShoppingLine("salt", None, "pantry"),
]


def test_shopping_list_text():
    assert render_shopping_list(LINES) == (
        "Shopping list: 4 items\n"
        "\n"
        "Produce\n"
        "  onion  2\n"
        "\n"
        "Dairy\n"
        "  milk   1 1/4 cup\n"
        "\n"
        "Pantry\n"
        "  flour  0.5 kg\n"
        "  salt\n"
    )


def test_empty_shopping_list():
    assert render_shopping_list([]) == "Nothing to buy.\n"


def test_shopping_csv(tmp_path):
    assert write_shopping_csv(LINES, tmp_path / "list.csv") == 4
    assert (tmp_path / "list.csv").read_text(encoding="utf-8") == (
        "item,quantity,unit\nonion,2,\nmilk,1 1/4,cup\nflour,0.5,kg\nsalt,,\n"
    )


def test_shopping_markdown():
    assert shopping_markdown(LINES[:2]) == "- [ ] onion — 2\n- [ ] milk — 1 1/4 cup\n"


def test_nutrition_report():
    summary = NutritionSummary("Toast", 2, {"kcal": 120, "protein_g": 4.1, "fat_g": 1.0, "carbs_g": 22.3}, ["jam"])
    assert render_nutrition(summary) == (
        "Toast, per serving (serves 2)\n"
        "  Energy            120 kcal\n"
        "  Protein           4.1 g\n"
        "  Fat               1.0 g\n"
        "  Carbohydrate     22.3 g\n"
        "Not counted: jam\n"
    )


def test_recipe_card(pancakes):
    card = render_recipe(pancakes)
    assert card.startswith("Fluffy Pancakes\nServes 4 - 25 min - breakfast, sweet\n\nIngredients\n")
    assert "  1 1/2 cup flour\n" in card
    assert "  2 egg\n" in card
    assert "  salt, to taste\n" in card
    assert "  1. Whisk the flour, sugar and salt.\n" in card


def test_plan_report(pancakes, soup):
    plan = Plan([MealEntry("tuesday", "lunch", soup, servings=4), MealEntry("monday", "breakfast", pancakes)])
    assert render_plan(plan, {"monday": 330, "tuesday": 150}) == (
        "Monday\n"
        "  breakfast  Fluffy Pancakes (serves 4)\n"
        "  energy     330 kcal per person\n"
        "\n"
        "Tuesday\n"
        "  lunch      Tomato Soup (serves 4)\n"
        "  energy     150 kcal per person\n"
    )
