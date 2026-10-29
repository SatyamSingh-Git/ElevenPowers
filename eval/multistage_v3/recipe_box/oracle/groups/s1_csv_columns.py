"""Stage 1: the shopping CSV has the columns item,aisle,quantity,unit."""
import csv

from recipebox.cli.main import main

SOUP = """title: Pea Soup
servings: 2

ingredients:
- 1 1/4 cup milk
- 300 g frozen peas
- 1 onion
- salt, to taste
"""


def run(home, *args):
    return main(["--home", str(home), *args])


def write_list(tmp_path):
    home = tmp_path / "home"
    (tmp_path / "soup.recipe").write_text(SOUP, encoding="utf-8")
    assert run(home, "add", str(tmp_path / "soup.recipe")) == 0
    (tmp_path / "plan.txt").write_text("monday lunch: Pea Soup\n", encoding="utf-8")
    assert run(home, "shop", str(tmp_path / "plan.txt"), "--csv", str(tmp_path / "list.csv")) == 0
    return (tmp_path / "list.csv").read_text(encoding="utf-8")


def test_header(tmp_path):
    assert write_list(tmp_path).splitlines()[0] == "item,aisle,quantity,unit"


def test_rows_line_up_with_the_header(tmp_path):
    rows = list(csv.reader(write_list(tmp_path).splitlines()))
    by_item = {row[0]: row for row in rows[1:]}
    assert by_item["milk"] == ["milk", "dairy", "1 1/4", "cup"]
    assert by_item["frozen peas"] == ["frozen peas", "frozen", "300", "g"]
    assert by_item["onion"] == ["onion", "produce", "1", ""]
    assert by_item["salt"] == ["salt", "pantry", "", ""]
