"""A quick look at a file's columns before deciding what to report on."""
from .errors import ReportError
from .numbers import format_number, parse_amount
from .table import render_table

HEADERS = ["column", "kind", "filled", "blank"]


def profile(rows):
    """Per column: whether every filled cell is a number, and how many cells are filled or blank."""
    columns = {}
    for row in rows:
        for name, text in row.items():
            stats = columns.setdefault(name, {"numeric": True, "filled": 0, "blank": 0})
            if not text.strip():
                stats["blank"] += 1
                continue
            stats["filled"] += 1
            if stats["numeric"]:
                try:
                    parse_amount(text)
                except ReportError:
                    stats["numeric"] = False
    return [[name, "number" if s["numeric"] and s["filled"] else "text", s["filled"], s["blank"]]
            for name, s in columns.items()]


def render_profile(rows, fmt="plain"):
    body = [[name, kind, format_number(filled, 0), format_number(blank, 0)]
            for name, kind, filled, blank in profile(rows)]
    return render_table(HEADERS, body, fmt)
