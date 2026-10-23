"""Strikethrough inside headings, links and lists; the table of contents shows the plain text."""
import re

from marklite import render, toc


def flatten(entries):
    for entry in entries:
        yield entry
        yield from flatten(getattr(entry, "children", None) or [])


def test_struck_heading():
    html = render("[TOC]\n\n## ~~Old~~ New\n")
    assert re.search(r'<h2 id="([^"]+)"><del>Old</del> New</h2>', html)
    heading_id = re.search(r'<h2 id="([^"]+)">', html).group(1)
    assert heading_id.endswith("old-new")
    assert f'<a href="#{heading_id}">Old New</a>' in html


def test_struck_heading_toc_entry():
    entries = list(flatten(toc("# ~~Draft~~ Final\n")))
    assert [(entry.title, entry.anchor.endswith("draft-final")) for entry in entries] == [("Draft Final", True)]


def test_strikethrough_in_links_and_lists():
    html = render("- ~~done~~ item\n- [~~old~~ link](/x)\n")
    assert "<li><del>done</del> item</li>" in html
    assert '<li><a href="/x"><del>old</del> link</a></li>' in html


def test_strikethrough_in_image_alt_is_plain():
    assert '<img src="p.png" alt="old pic" />' in render("![~~old~~ pic](p.png)\n")
