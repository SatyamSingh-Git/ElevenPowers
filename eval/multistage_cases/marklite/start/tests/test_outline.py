import pytest

from marklite import MarkliteError, Options, TocEntry, render, slugify, toc

DOCUMENT = """# Guide

[TOC]

## Install

## Usage *basics*

### Flags

## Usage basics
"""


def test_slugify():
    assert slugify("Hello, World!") == "hello-world"
    assert slugify("C++ & Rust") == "c-rust"
    assert slugify("Ünïcode Straße") == "ünïcode-strasse"
    assert slugify("???") == ""


def test_heading_ids_are_unique():
    html = render("# A\n# A\n# A-1\n# ???\n")
    assert 'id="a"' in html and 'id="a-1"' in html and 'id="a-1-1"' in html
    assert 'id="heading"' in html


def test_heading_ids_can_be_turned_off():
    assert render("# A\n", Options(heading_ids=False)) == "<h1>A</h1>\n"


def test_nested_headings_get_no_id():
    assert render("> # Quoted\n") == "<blockquote>\n<h1>Quoted</h1>\n</blockquote>\n"


def test_toc_entries():
    assert toc(DOCUMENT) == [
        TocEntry(1, "Guide", "guide"),
        TocEntry(2, "Install", "install"),
        TocEntry(2, "Usage basics", "usage-basics"),
        TocEntry(3, "Flags", "flags"),
        TocEntry(2, "Usage basics", "usage-basics-1"),
    ]


def test_toc_max_level():
    assert [entry.title for entry in toc(DOCUMENT, Options(toc_max_level=1))] == ["Guide"]


def test_toc_max_level_is_validated():
    with pytest.raises(MarkliteError, match="toc_max_level must be between 1 and 6"):
        Options(toc_max_level=7)


def test_toc_marker_renders_nested_lists():
    html = render(DOCUMENT)
    assert html.splitlines()[1] == (
        '<nav class="toc"><ul><li><a href="#guide">Guide</a><ul>'
        '<li><a href="#install">Install</a></li>'
        '<li><a href="#usage-basics">Usage basics</a><ul><li><a href="#flags">Flags</a></li></ul></li>'
        '<li><a href="#usage-basics-1">Usage basics</a></li>'
        "</ul></li></ul></nav>")


def test_toc_skipped_level_nests_under_closest_lower_entry():
    html = render("[TOC]\n\n# A\n### B\n## C\n")
    assert html.splitlines()[0] == (
        '<nav class="toc"><ul><li><a href="#a">A</a><ul>'
        '<li><a href="#b">B</a></li><li><a href="#c">C</a></li></ul></li></ul></nav>')


def test_empty_toc():
    assert render("[TOC]\n") == '<nav class="toc"></nav>\n'
