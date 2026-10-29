"""Stage 6: eggs are in the aisle `eggs` in the shopping CSV."""
import csv

from recipebox.cli.main import main

QUICHE = """title: Quiche
servings: 4

ingredients:
- 6 eggs
- 200 ml cream
- 100 g cheddar
- 1 onion
- 150 g flour
- 75 g butter
"""


def run(home, *args):
    return main(["--home", str(home), *args])


def test_egg_row_aisle(tmp_path):
    home = tmp_path / "home"
    (tmp_path / "quiche.recipe").write_text(QUICHE, encoding="utf-8")
    assert run(home, "add", str(tmp_path / "quiche.recipe")) == 0
    (tmp_path / "plan.txt").write_text("sunday lunch: Quiche\n", encoding="utf-8")
    assert run(home, "shop", str(tmp_path / "plan.txt"), "--csv", str(tmp_path / "list.csv")) == 0
    with open(tmp_path / "list.csv", newline="", encoding="utf-8") as handle:
        aisles = {row["item"]: row["aisle"] for row in csv.DictReader(handle)}
    assert aisles == {
        "egg": "eggs",
        "cream": "dairy",
        "cheddar": "dairy",
        "butter": "dairy",
        "onion": "produce",
        "flour": "pantry",
    }
