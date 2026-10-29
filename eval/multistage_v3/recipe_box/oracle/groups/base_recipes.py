"""Recipes in the library: showing, scaling, nutrition, and moving them to another library."""
import re

from recipebox.cli.main import main
from recipebox.services.nutrition import nutrition_for
from recipebox.storage.recipe_text import parse_recipe

PANCAKES = """title: Fluffy Pancakes
servings: 4
time: 25 min
tags: breakfast

ingredients:
- 1 1/2 cup flour
- 2 tbsp sugar
- 2 eggs
- 1 1/4 cup milk
- 30 g butter, melted
- salt, to taste

steps:
1. Whisk.
2. Fry.
"""

STEW = """title: Lentil Stew
servings: 2

ingredients:
- 200 g lentils
- 1 onion
- 2 carrots
- 750 ml vegetable stock
- 1 tbsp olive oil
"""


def run(home, *args):
    return main(["--home", str(home), *args])


def add_all(tmp_path, home):
    for name, text in [("pancakes", PANCAKES), ("stew", STEW)]:
        (tmp_path / f"{name}.recipe").write_text(text, encoding="utf-8")
        assert run(home, "add", str(tmp_path / f"{name}.recipe")) == 0


def nutrition_lines(text):
    return {match.group(1): match.group(2) for match in re.finditer(r"^\s+(\w+)\s+([\d.]+ \w+)$", text, re.M)}


def test_show_and_scale(tmp_path, capsys):
    home = tmp_path / "home"
    add_all(tmp_path, home)
    capsys.readouterr()
    assert run(home, "show", "fluffy-pancakes") == 0
    card = capsys.readouterr().out
    for line in ["  1 1/2 cup flour", "  2 egg", "  1 1/4 cup milk", "  30 g butter, melted", "  salt, to taste"]:
        assert line + "\n" in card
    assert run(home, "show", "fluffy-pancakes", "--servings", "2") == 0
    card = capsys.readouterr().out
    for line in ["  3/4 cup flour", "  1 egg", "  5/8 cup milk", "  15 g butter, melted"]:
        assert line + "\n" in card


def test_nutrition_command(tmp_path, capsys):
    home = tmp_path / "home"
    add_all(tmp_path, home)
    capsys.readouterr()
    assert run(home, "nutrition", "fluffy-pancakes") == 0
    out = capsys.readouterr().out
    assert out.splitlines()[0] == "Fluffy Pancakes, per serving (serves 4)"
    lines = nutrition_lines(out)
    assert lines["Energy"] == "331 kcal"
    assert lines["Protein"] == "10.5 g"
    assert lines["Fat"] == "11.4 g"
    assert lines["Carbohydrate"] == "46.0 g"
    assert run(home, "nutrition", "lentil-stew") == 0
    assert nutrition_lines(capsys.readouterr().out)["Energy"] == "485 kcal"


def test_nutrition_api():
    summary = nutrition_for(parse_recipe(PANCAKES))
    assert summary.per_serving["kcal"] == 331
    assert summary.per_serving["carbs_g"] == 46.0


def test_export_and_import_keep_recipes_whole(tmp_path, capsys):
    first, second = tmp_path / "first", tmp_path / "second"
    add_all(tmp_path, first)
    bundle = tmp_path / "bundle.json"
    assert run(first, "export", str(bundle)) == 0
    assert run(second, "import", str(bundle)) == 0
    capsys.readouterr()
    for command in (["list"], ["show", "fluffy-pancakes"], ["show", "lentil-stew", "--servings", "3"],
                    ["nutrition", "fluffy-pancakes"], ["nutrition", "lentil-stew"]):
        assert run(first, *command) == 0
        expected = capsys.readouterr().out
        assert run(second, *command) == 0
        assert capsys.readouterr().out == expected
