"""Stage 8: a library with number amounts reads back whole, and an older one with text amounts still opens."""
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

CARD_LINES = ["  2 1/4 cup flour", "  1/4 tsp salt", "  0.75 l milk", "  3 egg", "  1/2 cup butter", "  jam, to serve"]

AS_TEXT = {0.25: "1/4", 0.5: "1/2", 0.75: "3/4", 2.25: "2 1/4", 3: "3"}


def run(home, *args):
    return main(["--home", str(home), *args])


def rewrite_amounts(node, change):
    if isinstance(node, dict):
        if node.get("amount") is not None:
            node["amount"] = change(node["amount"])
        for value in node.values():
            rewrite_amounts(value, change)
    elif isinstance(node, list):
        for value in node:
            rewrite_amounts(value, change)


def add(tmp_path, home):
    (tmp_path / "scones.recipe").write_text(SCONES, encoding="utf-8")
    assert run(home, "add", str(tmp_path / "scones.recipe")) == 0


def test_number_amounts_read_back(tmp_path, capsys):
    home = tmp_path / "home"
    add(tmp_path, home)
    data = json.loads((home / "library.json").read_text(encoding="utf-8"))
    seen = []
    rewrite_amounts(data, lambda amount: seen.append(amount) or amount)
    assert all(type(amount) in (int, float) for amount in seen)
    capsys.readouterr()
    assert run(home, "show", "scones") == 0
    card = capsys.readouterr().out
    for line in CARD_LINES:
        assert line + "\n" in card
    assert run(home, "show", "scones", "--servings", "4") == 0
    assert "  1 1/8 cup flour\n" in capsys.readouterr().out


def test_older_text_amounts_still_open(tmp_path, capsys):
    home = tmp_path / "home"
    add(tmp_path, home)
    path = home / "library.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    rewrite_amounts(data, lambda amount: AS_TEXT[amount] if not isinstance(amount, str) else amount)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    capsys.readouterr()
    assert run(home, "show", "scones") == 0
    card = capsys.readouterr().out
    for line in CARD_LINES:
        assert line + "\n" in card
