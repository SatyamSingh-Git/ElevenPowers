"""Stage 7: `--limit 0` prints every match; a negative limit is refused."""
from recipebox.cli.main import main


def run(home, *args):
    return main(["--home", str(home), *args])


def fill(tmp_path, home, count):
    for number in range(count):
        path = tmp_path / f"stew{number}.recipe"
        path.write_text(f"title: Stew Number {number:02}\nservings: 2\n\ningredients:\n- 1 carrot\n", encoding="utf-8")
        assert run(home, "add", str(path)) == 0


def test_limit_zero_prints_everything(tmp_path, capsys):
    home = tmp_path / "home"
    fill(tmp_path, home, 40)
    capsys.readouterr()
    assert run(home, "search", "stew", "--limit", "0") == 0
    lines = capsys.readouterr().out.splitlines()
    assert len([line for line in lines if line.startswith("stew-number-")]) == 40
    assert not any(line.startswith("showing") for line in lines)


def test_negative_limit_is_refused(tmp_path, capsys):
    home = tmp_path / "home"
    fill(tmp_path, home, 2)
    capsys.readouterr()
    try:
        status = run(home, "search", "stew", "--limit", "-1")
    except SystemExit as stopped:
        # Refusing it while parsing the options is as good as refusing it later.
        status = stopped.code
    assert status != 0
    assert "--limit must be 0 or more" in capsys.readouterr().err
