from recipebox.cli.main import main
from recipebox.config import Settings, find_home, load_settings


def run(home, *args):
    return main(["--home", str(home.root), *args])


def test_add_list_show(home, recipe_files, capsys):
    assert run(home, "add", *map(str, recipe_files)) == 0
    assert capsys.readouterr().out == "added fluffy-pancakes\nadded tomato-soup\n"
    run(home, "list")
    assert capsys.readouterr().out == "fluffy-pancakes  Fluffy Pancakes\ntomato-soup      Tomato Soup\n"
    run(home, "show", "fluffy-pancakes", "--servings", "2")
    assert "  3/4 cup flour\n" in capsys.readouterr().out


def test_unknown_recipe(home, capsys):
    assert run(home, "show", "waffles") == 1
    assert capsys.readouterr().err == "error: no recipe with id waffles\n"


def test_add_twice(home, recipe_files, capsys):
    run(home, "add", str(recipe_files[0]))
    assert run(home, "add", str(recipe_files[0])) == 1
    assert "error: recipe fluffy-pancakes already exists" in capsys.readouterr().err
    assert run(home, "add", "--replace", str(recipe_files[0])) == 0


def test_search_limit(home, tmp_path, capsys):
    for number in range(12):
        path = tmp_path / f"r{number}.recipe"
        path.write_text(f"title: Soup {number:02}\nservings: 2\n\ningredients:\n- 1 onion\n", encoding="utf-8")
        run(home, "add", str(path))
    capsys.readouterr()
    run(home, "search", "soup")
    out = capsys.readouterr().out.splitlines()
    assert len(out) == 11
    assert out[-1] == "showing 10 of 12 matches"
    run(home, "search", "soup", "--limit", "3")
    assert capsys.readouterr().out.splitlines()[-1] == "showing 3 of 12 matches"
    assert run(home, "search", "soup", "--limit", "0") == 1
    assert capsys.readouterr().err == "error: --limit must be at least 1\n"


def test_pantry_commands(home, capsys):
    run(home, "pantry", "add", "flour", "500", "g")
    run(home, "pantry", "add", "salt")
    run(home, "pantry", "use", "flour", "200", "g")
    capsys.readouterr()
    run(home, "pantry", "list")
    assert capsys.readouterr().out == "flour  300 g\nsalt   staple\n"


def test_rename(home, recipe_files, capsys):
    run(home, "add", str(recipe_files[1]))
    assert run(home, "rename", "tomato-soup", "Roast Tomato Soup") == 0
    assert capsys.readouterr().out.endswith("tomato-soup is now roast-tomato-soup\n")


def test_home_and_settings(tmp_path):
    assert find_home(None, {"RECIPEBOX_HOME": str(tmp_path)}).root == tmp_path
    assert load_settings(tmp_path / "missing.ini") == Settings()
    (tmp_path / "recipebox.ini").write_text("[shopping]\nuse_pantry = no\n[plan]\nmeals = lunch, dinner\n")
    assert load_settings(tmp_path / "recipebox.ini") == Settings(use_pantry=False, suggest_meals=("lunch", "dinner"))
