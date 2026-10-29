"""Plain-text tables for the terminal and the printer."""


def table(headers, rows):
    """Lines of a left-aligned table; numbers are right-aligned."""
    rows = [[str(cell) for cell in row] for row in rows]
    widths = [len(header) for header in headers]
    for row in rows:
        widths = [max(width, len(cell)) for width, cell in zip(widths, row)]
    numeric = [all(_is_number(row[n]) for row in rows) and bool(rows) for n in range(len(headers))]

    def line(cells):
        parts = []
        for cell, width, right in zip(cells, widths, numeric):
            parts.append(cell.rjust(width) if right else cell.ljust(width))
        return "  ".join(parts).rstrip()

    return [line(headers), line(["-" * width for width in widths])] + [line(row) for row in rows]


def _is_number(text):
    return text.replace(".", "", 1).replace("%", "", 1).isdigit()


def percent(value):
    return f"{value:.0f}%"
