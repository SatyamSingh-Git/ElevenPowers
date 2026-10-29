"""Stage 7: search prints up to 25 matches by default."""
from recipebox.cli.main import main


def run(home, *args):
    return main(["--home", str(home), *args])


def fill(tmp_path, home, count):
    for number in range(count):
        path = tmp_path / f"soup{number}.recipe"
        path.write_text(f"title: Soup Number {number:02}\nservings: 2\n\ningredients:\n- 1 onion\n", encoding="utf-8")
        assert run(home, "add", str(path)) == 0


def matches(out):
    return [line for line in out.splitlines() if line.startswith("soup-number-")]


def test_default_limit(tmp_path, capsys):
    home = tmp_path / "home"
    fill(tmp_path, home, 30)
    capsys.readouterr()
    assert run(home, "search", "soup") == 0
    out = capsys.readouterr().out
    assert len(matches(out)) == 25
    assert out.splitlines()[-1] == "showing 25 of 30 matches"


def test_an_explicit_limit_still_applies(tmp_path, capsys):
    home = tmp_path / "home"
    fill(tmp_path, home, 30)
    capsys.readouterr()
    assert run(home, "search", "soup", "--limit", "12") == 0
    out = capsys.readouterr().out
    assert len(matches(out)) == 12
    assert out.splitlines()[-1] == "showing 12 of 30 matches"
