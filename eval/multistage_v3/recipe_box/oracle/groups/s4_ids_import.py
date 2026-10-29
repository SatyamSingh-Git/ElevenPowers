"""Stage 4: recipes moved to another library get the same clean ids there."""
from recipebox.cli.main import main


def run(home, *args):
    return main(["--home", str(home), *args])


def test_imported_recipes_get_clean_ids(tmp_path, capsys):
    first, second = tmp_path / "first", tmp_path / "second"
    for name, title in [("tea", "Tea, Hot!"), ("cafe", "Café au Lait")]:
        path = tmp_path / f"{name}.recipe"
        path.write_text(f"title: {title}\nservings: 1\n\ningredients:\n- 250 ml milk\n", encoding="utf-8")
        assert run(first, "add", str(path)) == 0
    assert run(first, "export", str(tmp_path / "bundle.json")) == 0
    capsys.readouterr()
    assert run(second, "import", str(tmp_path / "bundle.json")) == 0
    assert sorted(capsys.readouterr().out.split()) == sorted(["added", "cafe-au-lait", "added", "tea-hot"])
    assert run(second, "show", "tea-hot") == 0
    assert capsys.readouterr().out.startswith("Tea, Hot!\n")
    assert run(second, "show", "cafe-au-lait") == 0
    assert "  250 ml milk\n" in capsys.readouterr().out
