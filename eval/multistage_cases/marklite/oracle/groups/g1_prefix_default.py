"""Heading ids carry the section- prefix by default, and the table of contents follows."""
import json
import re

from marklite import render, toc
from marklite.cli import main


def flatten(entries):
    for entry in entries:
        yield entry
        yield from flatten(getattr(entry, "children", None) or [])


def test_default_prefix_on_heading_ids():
    html = render("# Search\n\n## Search\n\n## ???\n")
    assert re.findall(r'\sid="([^"]*)"', html) == ["section-search", "section-search-1", "section-heading"]


def test_table_of_contents_links_use_the_prefix():
    html = render("# Intro\n\n[TOC]\n\n## Intro\n")
    assert '<h1 id="section-intro">Intro</h1>' in html
    assert '<h2 id="section-intro-1">Intro</h2>' in html
    assert re.findall(r'href="([^"]*)"', html) == ["#section-intro", "#section-intro-1"]


def test_toc_entries_use_the_prefix():
    assert [entry.anchor for entry in flatten(toc("# Intro\n\n## Setup\n"))] == ["section-intro", "section-setup"]


def test_command_uses_the_prefix(tmp_path):
    source = tmp_path / "in.md"
    source.write_text("# Search\n", encoding="utf-8")
    out = tmp_path / "out.html"
    assert main([str(source), "-o", str(out)]) == 0
    assert out.read_text(encoding="utf-8") == '<h1 id="section-search">Search</h1>\n'
    assert main([str(source), "--json-toc", "-o", str(out)]) == 0
    assert "section-search" in json.dumps(json.loads(out.read_text(encoding="utf-8")))
