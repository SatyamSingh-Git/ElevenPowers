"""Plain-text tables for the terminal and for files people read."""


def render_table(headers, rows, *, right=()):
    """Columns named in `right` are right-aligned, which suits numbers and amounts."""
    cells = [[str(cell) for cell in row] for row in rows]
    widths = [max([len(header)] + [len(row[index]) for row in cells])
              for index, header in enumerate(headers)]

    def line(values):
        parts = []
        for header, width, value in zip(headers, widths, values):
            parts.append(value.rjust(width) if header in right else value.ljust(width))
        return "  ".join(parts).rstrip()

    rule = "  ".join("-" * width for width in widths)
    return "\n".join([line(headers), rule, *(line(row) for row in cells)])
