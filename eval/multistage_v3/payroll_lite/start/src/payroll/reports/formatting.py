"""Plain-text tables for the command line."""


def table(header, rows, numeric=()):
    """Columns sized to fit their widest cell; columns whose index is in `numeric` are right-aligned."""
    numeric = set(numeric)
    cells = [[str(cell) for cell in header]] + [[str(cell) for cell in row] for row in rows]
    widths = [max(len(row[index]) for row in cells) for index in range(len(header))]
    lines = []
    for row in cells:
        parts = [
            cell.rjust(widths[index]) if index in numeric else cell.ljust(widths[index])
            for index, cell in enumerate(row)
        ]
        lines.append("  ".join(parts).rstrip())
    return "\n".join(lines) + "\n"
