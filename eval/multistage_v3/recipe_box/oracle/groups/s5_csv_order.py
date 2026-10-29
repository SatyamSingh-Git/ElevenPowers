"""Stage 5: the shopping CSV lists items alphabetically by name."""
import csv

from recipebox.cli.main import main

CURRY = """title: Chicken Curry
servings: 4

ingredients:
- 500 g chicken breast
- 2 onions
- 3 cloves garlic
- 400 ml cream
- 300 g rice
- 200 g frozen peas
- 1 tbsp olive oil
- 2 tomatoes
"""


def run(home, *args):
    return main(["--home", str(home), *args])


def test_csv_rows_by_name(tmp_path):
    home = tmp_path / "home"
    (tmp_path / "curry.recipe").write_text(CURRY, encoding="utf-8")
    assert run(home, "add", str(tmp_path / "curry.recipe")) == 0
    (tmp_path / "plan.txt").write_text("friday dinner: Chicken Curry\n", encoding="utf-8")
    assert run(home, "shop", str(tmp_path / "plan.txt"), "--csv", str(tmp_path / "list.csv")) == 0
    with open(tmp_path / "list.csv", newline="", encoding="utf-8") as handle:
        items = [row["item"] for row in csv.DictReader(handle)]
    assert items == [
        "chicken breast", "cream", "frozen peas", "garlic", "olive oil", "onion", "rice", "tomato",
    ]
