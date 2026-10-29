"""Plain-text helpers shared by the reports."""
from ..core.units import format_value


def number(kind, value):
    return "-" if value is None else format_value(kind, value)


def signed(kind, value):
    text = format_value(kind, value)
    return text if text.startswith("-") else f"+{text}"


def label(kind):
    """A kind as people write it: ``soil_moisture`` reads ``soil moisture``."""
    return kind.replace("_", " ")


def heading(text):
    return f"{text}\n{'=' * len(text)}"


def table(headers, rows):
    """Left-aligned columns separated by two spaces."""
    cells = [[str(cell) for cell in row] for row in rows]
    widths = [len(header) for header in headers]
    for row in cells:
        widths = [max(width, len(cell)) for width, cell in zip(widths, row)]
    lines = [_line(headers, widths)]
    lines += [_line(row, widths) for row in cells]
    return "\n".join(lines)


def _line(cells, widths):
    return "  ".join(cell.ljust(width) for cell, width in zip(cells, widths)).rstrip()
