"""Stage 1: each CSV row carries the aisle code of its item."""
import csv

from recipebox.cli.main import main

BAKE = """title: Cheese Toast
servings: 2

ingredients:
- 4 slices bread
- 100 g cheddar
- 2 tomatoes
- 1 tbsp olive oil
- 1 tsp smoked paprika
- 2 slices bacon
"""


def run(home, *args):
    return main(["--home", str(home), *args])


def test_aisle_codes(tmp_path):
    home = tmp_path / "home"
    (tmp_path / "toast.recipe").write_text(BAKE, encoding="utf-8")
    assert run(home, "add", str(tmp_path / "toast.recipe")) == 0
    (tmp_path / "plan.txt").write_text("saturday lunch: Cheese Toast x4\n", encoding="utf-8")
    assert run(home, "shop", str(tmp_path / "plan.txt"), "--csv", str(tmp_path / "list.csv")) == 0
    with open(tmp_path / "list.csv", newline="", encoding="utf-8") as handle:
        aisles = {row["item"]: row["aisle"] for row in csv.DictReader(handle)}
    assert aisles == {
        "bread": "bakery",
        "cheddar": "dairy",
        "tomato": "produce",
        "olive oil": "pantry",
        "smoked paprika": "other",
        "bacon": "meat",
    }
