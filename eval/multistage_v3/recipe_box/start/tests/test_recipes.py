from fractions import Fraction

import pytest

from recipebox.core.ingredients import Ingredient, canonical_name, format_ingredient, parse_ingredient
from recipebox.core.quantity import Quantity
from recipebox.core.recipe import Recipe, recipe_id, validate
from recipebox.errors import RecipeError
from recipebox.storage.recipe_text import dump_recipe, parse_minutes, parse_recipe, parse_recipes


@pytest.mark.parametrize("text, name", [
    ("Eggs", "egg"), ("cherry tomatoes", "cherry tomato"), ("berries", "berry"), ("oats", "oats"),
    ("plain flour", "flour"), ("Scallions", "green onion"), ("molasses", "molasses"),
])
def test_canonical_name(text, name):
    assert canonical_name(text) == name


def test_parse_ingredient_with_unit_and_note():
    assert parse_ingredient("- 1 1/2 cups plain flour, sifted") == Ingredient(
        "flour", Quantity(Fraction(3, 2), "cup"), "sifted")


def test_parse_ingredient_count_and_no_amount():
    assert parse_ingredient("2 eggs") == Ingredient("egg", Quantity(Fraction(2), ""))
    assert parse_ingredient("salt, to taste") == Ingredient("salt", None, "to taste")


def test_unit_word_alone_is_a_name():
    assert parse_ingredient("2 cans") == Ingredient("can", Quantity(Fraction(2), ""))


def test_parse_ingredient_needs_a_name():
    with pytest.raises(RecipeError, match="ingredient has no name"):
        parse_ingredient("1 1/2")


def test_format_ingredient_reads_back():
    for line in ["1 1/2 cup flour, sifted", "2 egg", "salt, to taste", "3 clove garlic"]:
        assert format_ingredient(parse_ingredient(line)) == line


def test_recipe_id():
    assert recipe_id("Fluffy Pancakes") == "fluffy-pancakes"
    assert recipe_id("  Tomato   Soup ") == "tomato-soup"


def test_parse_recipe(pancakes):
    assert pancakes.title == "Fluffy Pancakes"
    assert pancakes.servings == 4
    assert pancakes.minutes == 25
    assert pancakes.tags == ("breakfast", "sweet")
    assert len(pancakes.ingredients) == 6
    assert pancakes.steps[0] == "Whisk the flour, sugar and salt."


def test_dump_and_parse_round_trip(pancakes):
    assert parse_recipe(dump_recipe(pancakes)) == pancakes


def test_several_recipes_in_one_file(pancakes, soup):
    text = dump_recipe(pancakes) + "---\n" + dump_recipe(soup)
    assert parse_recipes(text) == [pancakes, soup]


@pytest.mark.parametrize("text, minutes", [("25", 25), ("25 min", 25), ("1 h 30 min", 90), ("2 hours", 120)])
def test_parse_minutes(text, minutes):
    assert parse_minutes(text) == minutes


@pytest.mark.parametrize("text, message", [
    ("servings: 2\n\ningredients:\n- 1 egg\n", "missing title"),
    ("title: X\nservings: two\n\ningredients:\n- 1 egg\n", "servings must be a whole number"),
    ("title: X\nservings: 2\nflavour: good\n", "unknown field flavour"),
    ("title: X\nservings: 0\n\ningredients:\n- 1 egg\n", "servings must be between 1 and 100"),
    ("title: X\nservings: 2\n", "X has no ingredients"),
])
def test_parse_recipe_errors(text, message):
    with pytest.raises(RecipeError, match=message):
        parse_recipe(text)


def test_validate_limits():
    egg = (Ingredient("egg", Quantity(Fraction(1))),)
    with pytest.raises(RecipeError, match="longer than 80"):
        validate(Recipe("x" * 81, 2, egg))
    with pytest.raises(RecipeError, match="at most 10 tags"):
        validate(Recipe("Eggs", 2, egg, tags=tuple(str(n) for n in range(11))))
