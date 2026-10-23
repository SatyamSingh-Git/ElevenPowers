"""Laying out rows of text as plain-text or markdown tables."""
import re

from .errors import ReportError

FORMATS = ("plain", "markdown")
GAP = "  "
# 12, -1,234.50, $7.00, -€3.10, CHF 12.00: what a column has to hold to be right-aligned.
_NUMERIC = re.compile(r"-?(?:[^\d\s-][^\d-]{0,3})?\d[\d,]*(?:\.\d+)?")


def render_table(headers, rows, fmt="plain", align=None, totals=None):
    """``rows`` and ``totals`` are lists of cells; None prints as an empty cell.

    ``align`` holds "l" or "r" per column. Without it, a column whose cells all
    look like numbers is right-aligned and every other column left-aligned.
    """
    if fmt not in FORMATS:
        raise ReportError(f"unknown format: {fmt}")
    headers = [str(name) for name in headers]
    rows = [[_text(value) for value in row] for row in rows]
    if totals is not None:
        totals = [_text(value) for value in totals]
    for row in rows + ([totals] if totals else []):
        if len(row) != len(headers):
            raise ReportError(f"row has {len(row)} cells but the table has {len(headers)} columns")
    if align is None:
        align = [_guess([row[i] for row in rows]) for i in range(len(headers))]
    elif len(align) != len(headers) or set(align) - {"l", "r"}:
        raise ReportError(f"align needs 'l' or 'r' for each of {len(headers)} columns")
    if fmt == "markdown":
        return _markdown(headers, rows, align, totals)
    return _plain(headers, rows, align, totals)


def _text(value):
    return "" if value is None else str(value)


def _guess(cells):
    filled = [text for text in cells if text]
    return "r" if filled and all(_NUMERIC.fullmatch(text) for text in filled) else "l"


def _pad(text, width, side):
    return text.rjust(width) if side == "r" else text.ljust(width)


def _widths(headers, body, least=1):
    return [max(least, *(len(row[i]) for row in [headers, *body])) for i in range(len(headers))]


def _plain(headers, rows, align, totals):
    widths = _widths(headers, rows + ([totals] if totals else []))

    def line(cells):
        return GAP.join(_pad(text, width, side) for text, width, side in zip(cells, widths, align)).rstrip()

    rule = GAP.join("-" * width for width in widths)
    lines = [line(headers), rule, *(line(row) for row in rows)]
    if totals:
        lines += [rule, line(totals)]
    return "\n".join(lines) + "\n"


def _markdown(headers, rows, align, totals):
    headers = [_escape(text) for text in headers]
    body = [[_escape(text) for text in row] for row in rows + ([totals] if totals else [])]
    widths = _widths(headers, body, least=3)

    def line(cells):
        return "| " + " | ".join(_pad(text, width, side) for text, width, side in zip(cells, widths, align)) + " |"

    rule = "| " + " | ".join("-" * (width - 1) + ":" if side == "r" else "-" * width
                             for width, side in zip(widths, align)) + " |"
    return "\n".join([line(headers), rule, *(line(row) for row in body)]) + "\n"


def _escape(text):
    return text.replace("|", "\\|")
