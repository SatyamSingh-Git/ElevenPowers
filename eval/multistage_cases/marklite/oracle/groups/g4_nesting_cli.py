"""Pathologically deep input is reported as an error everywhere, never a RecursionError."""
import pytest

from marklite import MarkliteError, render, toc
from marklite.cli import main

DEEP = "# Title\n\n" + ">" * 5000 + " pasted by accident\n"


def test_render_raises_marklite_error():
    with pytest.raises(MarkliteError) as raised:
        render(DEEP)
    assert str(raised.value) == "line 3: nesting deeper than 32 levels"


def test_toc_raises_marklite_error():
    with pytest.raises(MarkliteError, match="nesting deeper than 32 levels"):
        toc(DEEP)


def test_deep_lists_raise_marklite_error():
    deep = "".join(" " * (2 * level) + "- x\n" for level in range(600))
    with pytest.raises(MarkliteError, match="nesting deeper than 32 levels"):
        render(deep)


def test_command_reports_the_error(tmp_path, capsys):
    source = tmp_path / "deep.md"
    source.write_text(DEEP, encoding="utf-8")
    out = tmp_path / "out.html"
    assert main([str(source), "-o", str(out)]) == 1
    captured = capsys.readouterr()
    assert captured.err.strip() == "error: line 3: nesting deeper than 32 levels"
    assert "Traceback" not in captured.err
    assert main([str(source), "--json-toc"]) == 1
    assert "nesting deeper than 32 levels" in capsys.readouterr().err
