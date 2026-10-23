"""Nesting is limited to 32 levels; deeper raises MarkliteError with the offending line."""
import pytest

from marklite import MarkliteError, parse, render


def test_thirty_two_levels_render():
    html = render(">" * 32 + " deep\n")
    assert html.count("<blockquote>") == 32
    assert "<p>deep</p>" in html


def test_thirty_three_levels_raise():
    with pytest.raises(MarkliteError) as raised:
        render(">" * 33 + " deep\n")
    assert "nesting deeper than 32 levels" in str(raised.value)
    assert raised.value.line == 1


def test_error_names_the_line():
    with pytest.raises(MarkliteError) as raised:
        parse("intro\n\n" + ">" * 40 + " x\n")
    assert raised.value.line == 3
    assert str(raised.value) == "line 3: nesting deeper than 32 levels"


def test_lists_count_towards_the_limit():
    shallow = "".join("  " * level + "- item\n" for level in range(20))
    assert render(shallow).count("<ul>") == 20
    deep = "".join("  " * level + "- item\n" for level in range(40))
    with pytest.raises(MarkliteError, match="nesting deeper than 32 levels"):
        render(deep)

    def quoted_lists(quotes, lists):
        return "".join(">" * quotes + " " + "  " * level + "- item\n" for level in range(lists))

    html = render(quoted_lists(10, 10))
    assert html.count("<blockquote>") == 10 and html.count("<ul>") == 10
    with pytest.raises(MarkliteError, match="nesting deeper than 32 levels"):
        render(quoted_lists(20, 20))
