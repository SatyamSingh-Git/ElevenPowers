import json

import pytest

from marklite import MarkliteError, render
from marklite.cli import main

DOCUMENT = "# Title\n\n[TOC]\n\n## Part\n\n### Detail\n\ntext\n"


@pytest.fixture
def source(tmp_path):
    path = tmp_path / "in.md"
    path.write_text(DOCUMENT, encoding="utf-8")
    return path


def test_renders_to_output_file(source, tmp_path):
    out = tmp_path / "out.html"
    assert main([str(source), "-o", str(out)]) == 0
    assert out.read_text(encoding="utf-8") == render(DOCUMENT)


def test_renders_to_stdout(source, capsys):
    assert main([str(source), "--no-ids"]) == 0
    assert capsys.readouterr().out.startswith("<h1>Title</h1>\n")


def test_json_toc(source, capsys):
    assert main([str(source), "--json-toc", "--toc-level", "2"]) == 0
    assert json.loads(capsys.readouterr().out) == [
        {"level": 1, "title": "Title", "anchor": "title"},
        {"level": 2, "title": "Part", "anchor": "part"},
    ]


def test_missing_file(tmp_path, capsys):
    assert main([str(tmp_path / "nope.md")]) == 1
    assert capsys.readouterr().err == f"error: cannot read {tmp_path / 'nope.md'}\n"


def test_bad_toc_level(source, capsys):
    assert main([str(source), "--toc-level", "0"]) == 1
    assert capsys.readouterr().err == "error: toc_max_level must be between 1 and 6\n"


def test_input_size_limit(tmp_path, capsys):
    path = tmp_path / "big.md"
    path.write_text("a" * 1_000_001, encoding="utf-8")
    assert main([str(path)]) == 1
    assert capsys.readouterr().err == "error: input exceeds 1000000 characters\n"
    with pytest.raises(MarkliteError):
        render("a" * 1_000_001)
