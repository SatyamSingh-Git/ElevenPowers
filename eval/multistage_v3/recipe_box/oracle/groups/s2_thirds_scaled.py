"""Stage 2: scaling that lands on thirds shows thirds."""
from recipebox.cli.main import main

PORRIDGE = """title: Porridge
servings: 3

ingredients:
- 1 cup oats
- 2 tbsp honey
- 3 cup milk
"""


def run(home, *args):
    return main(["--home", str(home), *args])


def test_scaled_thirds(tmp_path, capsys):
    home = tmp_path / "home"
    (tmp_path / "porridge.recipe").write_text(PORRIDGE, encoding="utf-8")
    assert run(home, "add", str(tmp_path / "porridge.recipe")) == 0
    capsys.readouterr()
    assert run(home, "show", "porridge", "--servings", "1") == 0
    card = capsys.readouterr().out
    for line in ["  1/3 cup oats", "  2/3 tbsp honey", "  1 cup milk"]:
        assert line + "\n" in card
    assert run(home, "show", "porridge", "--servings", "4") == 0
    card = capsys.readouterr().out
    for line in ["  1 1/3 cup oats", "  2 2/3 tbsp honey", "  4 cup milk"]:
        assert line + "\n" in card
