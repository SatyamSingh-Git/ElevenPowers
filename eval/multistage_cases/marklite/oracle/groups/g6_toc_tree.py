"""toc() returns a tree: the outermost entries, each with a children list."""
from marklite import Options, toc

DOCUMENT = """# Guide

## Install

## Usage

### Flags

# FAQ
"""


def shape(entries):
    return [(entry.level, entry.title, shape(entry.children)) for entry in entries]


def test_top_level_entries_hold_their_children():
    assert shape(toc(DOCUMENT)) == [
        (1, "Guide", [(2, "Install", []), (2, "Usage", [])]),
        (1, "FAQ", []),
    ]


def test_deeper_levels_nest_further():
    assert shape(toc(DOCUMENT, Options(toc_max_level=3))) == [
        (1, "Guide", [(2, "Install", []), (2, "Usage", [(3, "Flags", [])])]),
        (1, "FAQ", []),
    ]


def test_entries_keep_level_title_and_anchor():
    guide = toc(DOCUMENT)[0]
    assert (guide.level, guide.title) == (1, "Guide")
    assert guide.anchor == "section-guide"
    assert [child.anchor for child in guide.children] == ["section-install", "section-usage"]


def test_leaves_have_empty_children():
    faq = toc(DOCUMENT)[1]
    assert faq.children == []
    assert toc("# Only\n")[0].children == []
