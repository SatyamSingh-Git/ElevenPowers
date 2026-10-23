"""The id_prefix option: a custom prefix, or none, applied to ids and anchors alike."""
import re

from marklite import Options, render, toc


def flatten(entries):
    for entry in entries:
        yield entry
        yield from flatten(getattr(entry, "children", None) or [])


def test_custom_prefix():
    options = Options(id_prefix="doc-")
    html = render("[TOC]\n\n# Search\n\n## Search\n", options)
    assert re.findall(r'\sid="([^"]*)"', html) == ["doc-search", "doc-search-1"]
    assert re.findall(r'href="([^"]*)"', html) == ["#doc-search", "#doc-search-1"]
    assert [entry.anchor for entry in flatten(toc("# Search\n", options))] == ["doc-search"]


def test_empty_prefix_gives_bare_slugs():
    options = Options(id_prefix="")
    html = render("[TOC]\n\n# Search\n\n## ???\n", options)
    assert re.findall(r'\sid="([^"]*)"', html) == ["search", "heading"]
    assert re.findall(r'href="([^"]*)"', html) == ["#search", "#heading"]
    assert [entry.anchor for entry in flatten(toc("# Search\n", options))] == ["search"]


def test_default_is_section():
    assert Options().id_prefix == "section-"


def test_prefix_does_not_change_numbering():
    html = render("# A\n# A-1\n# A\n", Options(id_prefix="x-"))
    assert re.findall(r'\sid="([^"]*)"', html) == ["x-a", "x-a-1", "x-a-2"]
