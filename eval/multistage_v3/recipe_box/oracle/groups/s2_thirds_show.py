"""Stage 2: thirds in a recipe are shown as thirds."""
from recipebox.cli.main import main

CAKE = """title: Mug Cake
servings: 1

ingredients:
- 1/3 cup sugar
- 2/3 cup milk
- 1 1/3 cup flour
- 1/2 tsp baking powder
"""


def run(home, *args):
    return main(["--home", str(home), *args])


def test_show_prints_thirds(tmp_path, capsys):
    home = tmp_path / "home"
    (tmp_path / "cake.recipe").write_text(CAKE, encoding="utf-8")
    assert run(home, "add", str(tmp_path / "cake.recipe")) == 0
    capsys.readouterr()
    assert run(home, "show", "mug-cake") == 0
    card = capsys.readouterr().out
    for line in ["  1/3 cup sugar", "  2/3 cup milk", "  1 1/3 cup flour", "  1/2 tsp baking powder"]:
        assert line + "\n" in card
