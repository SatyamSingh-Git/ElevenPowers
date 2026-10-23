"""Tree building at the edges: skipped levels, documents that start deep, limits and duplicates."""
from marklite import Options, render, toc


def shape(entries):
    return [(entry.title, shape(entry.children)) for entry in entries]


def test_skipped_level_nests_under_closest_lower_entry():
    entries = toc("# A\n### B\n## C\n### D\n", Options(toc_max_level=3))
    assert shape(entries) == [("A", [("B", []), ("C", [("D", [])])])]


def test_document_starting_below_level_one():
    assert shape(toc("## A\n### A1\n# B\n## B1\n", Options(toc_max_level=3))) == [
        ("A", [("A1", [])]), ("B", [("B1", [])])]


def test_unlisted_levels_are_left_out_of_the_tree():
    entries = toc("# A\n### Deep\n## C\n")
    assert shape(entries) == [("A", [("C", [])])]
    assert entries[0].children[0].anchor == "section-c"


def test_duplicate_anchors_in_the_tree():
    entries = toc("# A\n## Same\n# B\n## Same\n")
    assert [child.anchor for entry in entries for child in entry.children] == ["section-same", "section-same-1"]


def test_empty_document_has_no_entries():
    assert toc("just text\n") == []
    assert render("[TOC]\n") == '<nav class="toc"></nav>\n'


def test_siblings_after_a_nested_entry():
    assert shape(toc("# A\n## B\n# C\n")) == [("A", [("B", [])]), ("C", [])]
