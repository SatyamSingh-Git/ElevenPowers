"""Stage 8: library.json saves ingredient amounts as JSON numbers, and null when there is none."""
import json

from recipebox.cli.main import main

SCONES = """title: Scones
servings: 8

ingredients:
- 2 1/4 cup flour
- 1/4 tsp salt
- 0.75 l milk
- 3 eggs
- 1/2 cup butter
- jam, to serve
"""


def run(home, *args):
    return main(["--home", str(home), *args])


def amounts(home):
    data = json.loads((home / "library.json").read_text(encoding="utf-8"))
    found = []

    def walk(node):
        if isinstance(node, dict):
            if "amount" in node:
                found.append(node["amount"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(data)
    return found


def test_amounts_are_numbers(tmp_path):
    home = tmp_path / "home"
    (tmp_path / "scones.recipe").write_text(SCONES, encoding="utf-8")
    assert run(home, "add", str(tmp_path / "scones.recipe")) == 0
    found = amounts(home)
    assert len(found) == 6
    numbers = [value for value in found if value is not None]
    assert all(type(value) in (int, float) for value in numbers)
    assert sorted(numbers) == [0.25, 0.5, 0.75, 2.25, 3]
    assert found.count(None) == 1
