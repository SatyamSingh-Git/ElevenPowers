"""The command's table of contents follows the two-level default too."""
import json
import re

from marklite import Options, render
from marklite.cli import main

DOCUMENT = "# Top\n\n[TOC]\n\n## Middle\n\n### Low\n\n## Middle two\n"


def walk_json(value):
    if isinstance(value, dict):
        if "title" in value:
            yield value
        for item in value.values():
            yield from walk_json(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_json(item)


def run(tmp_path, *flags):
    source = tmp_path / "in.md"
    source.write_text(DOCUMENT, encoding="utf-8")
    out = tmp_path / "out.txt"
    assert main([str(source), "-o", str(out), *flags]) == 0
    return out.read_text(encoding="utf-8")


def test_command_default_leaves_out_level_three(tmp_path):
    html = run(tmp_path)
    nav = re.search(r'<nav class="toc">.*?</nav>', html, re.S).group()
    assert re.findall(r">([^<>]+)</a>", nav) == ["Top", "Middle", "Middle two"]
    assert html == render(DOCUMENT)


def test_command_json_default_leaves_out_level_three(tmp_path):
    entries = list(walk_json(json.loads(run(tmp_path, "--json-toc"))))
    assert "Low" not in [entry["title"] for entry in entries]
    assert {entry["level"] for entry in entries} == {1, 2}


def test_command_toc_level_flag_still_works(tmp_path):
    html = run(tmp_path, "--toc-level", "3")
    assert html == render(DOCUMENT, Options(toc_max_level=3))
    assert ">Low</a>" in html
