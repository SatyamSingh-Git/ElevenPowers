"""Plain text tables for the terminal and the printer."""


def table(headers, rows, right=()):
    """Columns padded to their widest cell; columns named in `right` are right-aligned."""
    cells = [[str(value) for value in row] for row in rows]
    widths = [len(header) for header in headers]
    for row in cells:
        widths = [max(width, len(cell)) for width, cell in zip(widths, row)]

    def line(values):
        padded = [value.rjust(width) if header in right else value.ljust(width)
                  for header, value, width in zip(headers, values, widths)]
        return "  ".join(padded).rstrip()

    rule = "  ".join("-" * width for width in widths)
    return "\n".join([line(list(headers)), rule] + [line(row) for row in cells])


def amount_line(label, amount, width=48):
    """`label` and `amount` on one line, the amount flush right."""
    return f"{label}{amount.rjust(width - len(label))}"
