"""A week's shopping, end to end: plan file, printed list, CSV, restock, and shopping again."""
from recipebox.cli.main import main

PANCAKES = """title: Fluffy Pancakes
servings: 4
time: 25 min

ingredients:
- 1 1/2 cup flour
- 2 tbsp sugar
- 2 eggs
- 1 1/4 cup milk
- 30 g butter
- salt, to taste
"""

MAC = """title: Mac & Cheese
servings: 4

ingredients:
- 400 g macaroni
- 200 g cheddar, grated
- 2 cup milk
- 40 g butter
"""

SOUP = """title: Tomato Soup
servings: 2

ingredients:
- 6 tomatoes
- 1 onion
- 2 cloves garlic
- 2 tbsp olive oil
- 500 ml vegetable stock
- 4 slices bread
- salt, to taste
"""

PLAN = """monday breakfast: Fluffy Pancakes
monday dinner: Mac & Cheese
tuesday lunch: Tomato Soup x4
wednesday dinner: Mac & Cheese
"""

WALK = ["Produce", "Bakery", "Dairy", "Meat", "Pantry", "Frozen", "Other"]


def run(home, *args):
    return main(["--home", str(home), *args])


def setup(tmp_path, capsys):
    home = tmp_path / "home"
    for name, text in [("pancakes", PANCAKES), ("mac", MAC), ("soup", SOUP)]:
        (tmp_path / f"{name}.recipe").write_text(text, encoding="utf-8")
        assert run(home, "add", str(tmp_path / f"{name}.recipe")) == 0
    (tmp_path / "plan.txt").write_text(PLAN, encoding="utf-8")
    assert run(home, "pantry", "add", "salt") == 0
    assert run(home, "pantry", "add", "macaroni", "300", "g") == 0
    capsys.readouterr()
    return home, tmp_path / "plan.txt"


def sections(text):
    lines = text.splitlines()
    found = []
    for line in lines[1:]:
        if not line.strip():
            continue
        if line.startswith(" "):
            found[-1][1].append(line.strip())
        else:
            found.append((line, []))
    return lines[0], found


def item(found, name):
    for heading, items in found:
        for line in items:
            if line == name or line.startswith(name + " "):
                return heading, line[len(name):].strip()
    return None


def test_printed_list_has_one_heading_per_aisle(tmp_path, capsys):
    home, plan = setup(tmp_path, capsys)
    assert run(home, "shop", str(plan)) == 0
    title, found = sections(capsys.readouterr().out)
    assert title == "Shopping list: 13 items"
    headings = [heading for heading, _ in found]
    assert len(headings) == len(set(headings))
    known = [heading for heading in headings if heading in WALK]
    assert known == sorted(known, key=WALK.index)
    assert item(found, "garlic") == ("Produce", "4 clove")
    assert item(found, "tomato") == ("Produce", "12")
    assert item(found, "onion") == ("Produce", "2")
    assert item(found, "bread") == ("Bakery", "8 slice")
    assert item(found, "milk") == ("Dairy", "5 1/4 cup")
    assert item(found, "butter") == ("Dairy", "110 g")
    assert item(found, "cheddar") == ("Dairy", "400 g")
    assert item(found, "flour") == ("Pantry", "1 1/2 cup")
    assert item(found, "macaroni") == ("Pantry", "500 g")
    assert item(found, "olive oil") == ("Pantry", "4 tbsp")
    assert item(found, "sugar") == ("Pantry", "2 tbsp")
    assert item(found, "vegetable stock") == ("Pantry", "1 l")
    assert item(found, "egg")[1] == "2"
    assert item(found, "salt") is None


def test_restocking_what_was_bought_covers_the_plan(tmp_path, capsys):
    home, plan = setup(tmp_path, capsys)
    bought = tmp_path / "bought.csv"
    assert run(home, "shop", str(plan), "--csv", str(bought)) == 0
    assert run(home, "pantry", "restock", str(bought)) == 0
    capsys.readouterr()
    assert run(home, "pantry", "list") == 0
    pantry = {line.split()[0]: line.split(None, 1)[1].strip() for line in capsys.readouterr().out.splitlines()
              if line.split()[0] in ("macaroni", "milk", "egg", "salt")}
    assert pantry == {"macaroni": "800 g", "milk": "5 1/4 cup", "egg": "2", "salt": "staple"}
    assert run(home, "shop", str(plan)) == 0
    assert capsys.readouterr().out == "Nothing to buy.\n"
