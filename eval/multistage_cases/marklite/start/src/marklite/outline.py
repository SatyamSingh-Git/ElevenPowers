"""The table of contents: which headings it lists, their anchors, and its HTML."""
from typing import NamedTuple

from .blocks import Heading
from .escape import escape
from .inline import parse_inline, plain_text
from .slug import Slugger

TOC_MARKER = "[TOC]"


class TocEntry(NamedTuple):
    level: int
    title: str
    anchor: str


def build_toc(document, options):
    """Entries for the top-level headings down to options.toc_max_level, in document order."""
    slugger = Slugger()
    entries = []
    for node in document.children:
        if not isinstance(node, Heading):
            continue
        title = plain_text(parse_inline(node.text))
        # Every heading takes its slug, listed or not, so duplicates number the same way the ids do.
        anchor = slugger.slug(title)
        if node.level <= options.toc_max_level:
            entries.append(TocEntry(node.level, title, anchor))
    return entries


def render_toc(entries):
    """Nested <ul> lists: an entry goes under the closest earlier entry with a lower level."""
    parts = ['<nav class="toc">']
    if entries:
        parts.append("<ul>")
    open_items = []  # [level, has_child_list] for each <li> not yet closed
    for entry in entries:
        while open_items and open_items[-1][0] >= entry.level:
            _close(parts, open_items.pop())
        if open_items:
            parent = open_items[-1]
            if not parent[1]:
                parts.append("<ul>")
                parent[1] = True
        parts.append(f'<li><a href="#{escape(entry.anchor)}">{escape(entry.title)}</a>')
        open_items.append([entry.level, False])
    while open_items:
        _close(parts, open_items.pop())
    if entries:
        parts.append("</ul>")
    parts.append("</nav>")
    return "".join(parts)


def _close(parts, item):
    parts.append("</ul></li>" if item[1] else "</li>")
