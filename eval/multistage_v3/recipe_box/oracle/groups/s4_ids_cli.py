"""Stage 4: ids made from titles use only a-z, 0-9 and dashes."""
from recipebox.cli.main import main

TITLES = {
    "mac": "Mac & Cheese",
    "brulee": "Crème Brûlée!",
    "fish": "  Fish, Chips & Peas  ",
    "soup": "15-Minute Soup",
}


def run(home, *args):
    return main(["--home", str(home), *args])


def add(tmp_path, home):
    for name, title in TITLES.items():
        path = tmp_path / f"{name}.recipe"
        path.write_text(f"title: {title}\nservings: 2\n\ningredients:\n- 1 egg\n", encoding="utf-8")
        assert run(home, "add", str(path)) == 0


def test_add_prints_clean_ids(tmp_path, capsys):
    add(tmp_path, tmp_path / "home")
    assert capsys.readouterr().out.split() == [
        "added", "mac-cheese", "added", "creme-brulee", "added", "fish-chips-peas", "added", "15-minute-soup",
    ]


def test_clean_ids_work_on_the_command_line(tmp_path, capsys):
    home = tmp_path / "home"
    add(tmp_path, home)
    capsys.readouterr()
    assert run(home, "list") == 0
    assert [line.split()[0] for line in capsys.readouterr().out.splitlines()] == [
        "15-minute-soup", "creme-brulee", "fish-chips-peas", "mac-cheese",
    ]
    assert run(home, "show", "creme-brulee") == 0
    assert capsys.readouterr().out.startswith("Crème Brûlée!\n")
    assert run(home, "show", "mac-cheese", "--servings", "4") == 0
    assert "  2 egg\n" in capsys.readouterr().out
