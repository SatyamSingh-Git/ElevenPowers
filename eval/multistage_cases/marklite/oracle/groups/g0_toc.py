"""Heading ids and the table of contents agree, through render, toc() and the command."""
from html.parser import HTMLParser
import json
import re

from marklite import render, toc
from marklite.cli import main

DOCUMENT = """# Guide

[TOC]

## Install

Run the installer.

## Usage *basics*

### Flags

## Usage basics

# FAQ &amp; Notes

## `run` command
"""

LISTED = ["Guide", "Install", "Usage basics", "Usage basics", "FAQ & Notes", "run command"]


def flatten(entries):
    for entry in entries:
        yield entry
        yield from flatten(getattr(entry, "children", None) or [])


def walk_json(value):
    if isinstance(value, dict):
        if "title" in value:
            yield value
        for item in value.values():
            yield from walk_json(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_json(item)


def heading_ids(html):
    return re.findall(r'<h[1-6][^>]*\sid="([^"]*)"', html)


class NavLinks(HTMLParser):
    """(href, text, list depth) for every link inside the toc nav."""

    def __init__(self):
        super().__init__()
        self.in_nav = False
        self.depth = 0
        self.links = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == "nav":
            self.in_nav = True
        elif self.in_nav and tag == "ul":
            self.depth += 1
        elif self.in_nav and tag == "a":
            self.current = [dict(attrs)["href"], "", self.depth]

    def handle_endtag(self, tag):
        if tag == "nav":
            self.in_nav = False
        elif self.in_nav and tag == "ul":
            self.depth -= 1
        elif self.in_nav and tag == "a" and self.current:
            self.links.append(tuple(self.current))
            self.current = None

    def handle_data(self, data):
        if self.current is not None:
            self.current[1] += data


def nav_links(html):
    parser = NavLinks()
    parser.feed(html)
    parser.close()
    return parser.links


def test_toc_links_point_at_heading_ids():
    html = render(DOCUMENT)
    ids = heading_ids(html)
    assert len(ids) == 7 and len(set(ids)) == 7
    links = nav_links(html)
    assert links
    for href, _, _ in links:
        assert href.startswith("#") and href[1:] in ids


def test_toc_titles_and_nesting():
    links = [(text, depth) for _, text, depth in nav_links(render(DOCUMENT)) if text != "Flags"]
    assert links == [("Guide", 1), ("Install", 2), ("Usage basics", 2), ("Usage basics", 2),
                     ("FAQ & Notes", 1), ("run command", 2)]


def test_toc_entries_match_heading_ids():
    html = render(DOCUMENT)
    ids = heading_ids(html)
    entries = [entry for entry in flatten(toc(DOCUMENT)) if entry.level <= 2]
    assert [entry.title for entry in entries] == LISTED
    assert [entry.level for entry in entries] == [1, 2, 2, 2, 1, 2]
    anchors = [entry.anchor for entry in entries]
    assert all(anchor in ids for anchor in anchors)
    assert len(set(anchors)) == len(anchors)
    assert anchors[2].endswith("usage-basics") and anchors[3].endswith("usage-basics-1")


def test_duplicate_numbering_counts_unlisted_headings():
    text = "[TOC]\n\n# A\n### Same\n## Same\n"
    html = render(text)
    ids = heading_ids(html)
    hrefs = [href[1:] for href, _, _ in nav_links(html)]
    assert all(href in ids for href in hrefs)
    same = [entry for entry in flatten(toc(text)) if entry.title == "Same" and entry.level == 2]
    assert len(same) == 1 and same[0].anchor == ids[2] and same[0].anchor.endswith("same-1")


def test_command_json_toc_lists_every_heading(tmp_path):
    source = tmp_path / "guide.md"
    source.write_text(DOCUMENT, encoding="utf-8")
    out = tmp_path / "toc.json"
    assert main([str(source), "--json-toc", "-o", str(out)]) == 0
    entries = [entry for entry in walk_json(json.loads(out.read_text(encoding="utf-8")))
               if entry["level"] <= 2]
    assert [entry["title"] for entry in entries] == LISTED
    ids = heading_ids(render(DOCUMENT))
    assert all(entry["anchor"] in ids for entry in entries)
