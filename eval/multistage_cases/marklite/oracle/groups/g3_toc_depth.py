"""The table of contents lists levels 1 and 2 by default; deeper levels on request."""
import re

from marklite import Options, render, toc

DOCUMENT = "# Top\n\n[TOC]\n\n## Middle\n\n### Low\n\n#### Lower\n\n## Middle two\n"


def flatten(entries):
    for entry in entries:
        yield entry
        yield from flatten(getattr(entry, "children", None) or [])


def nav(html):
    return re.search(r'<nav class="toc">.*?</nav>', html, re.S).group()


def test_default_is_two():
    assert Options().toc_max_level == 2


def test_toc_lists_two_levels_by_default():
    entries = list(flatten(toc(DOCUMENT)))
    assert [(entry.level, entry.title) for entry in entries] == [(1, "Top"), (2, "Middle"), (2, "Middle two")]


def test_rendered_toc_lists_two_levels_by_default():
    html = render(DOCUMENT)
    assert re.findall(r">([^<>]+)</a>", nav(html)) == ["Top", "Middle", "Middle two"]
    assert re.search(r'<h3 id="[^"]+">Low</h3>', html)


def test_deeper_levels_on_request():
    entries = list(flatten(toc(DOCUMENT, Options(toc_max_level=3))))
    assert [entry.title for entry in entries] == ["Top", "Middle", "Low", "Middle two"]
    html = render(DOCUMENT, Options(toc_max_level=4))
    assert re.findall(r">([^<>]+)</a>", nav(html)) == ["Top", "Middle", "Low", "Lower", "Middle two"]
