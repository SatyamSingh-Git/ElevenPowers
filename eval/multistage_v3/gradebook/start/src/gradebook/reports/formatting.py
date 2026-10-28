"""Formatters: a Table as text, CSV or Markdown, chosen by name with `--format`."""
import csv
import io

from ..errors import UnknownFormat


def render_text(table):
    widths = [len(column) for column in table.columns]
    for row in table.rows:
        widths = [max(width, len(cell)) for width, cell in zip(widths, row)]

    def line(cells):
        padded = [cell.rjust(width) if column in table.numeric else cell.ljust(width)
                  for column, cell, width in zip(table.columns, cells, widths)]
        return "  ".join(padded).rstrip()

    out = [table.title, ""] if table.title else []
    out.append(line(table.columns))
    out.append("  ".join("-" * width for width in widths))
    out.extend(line(row) for row in table.rows)
    if table.notes:
        out.append("")
        out.extend(table.notes)
    return "\n".join(out) + "\n"


def render_csv(table):
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(table.columns)
    writer.writerows(table.rows)
    return buffer.getvalue()


def render_markdown(table):
    def escape(cell):
        return cell.replace("|", "\\|")

    out = [f"## {table.title}", ""] if table.title else []
    out.append("| " + " | ".join(escape(column) for column in table.columns) + " |")
    out.append("|" + "|".join("---:" if column in table.numeric else "---" for column in table.columns) + "|")
    out.extend("| " + " | ".join(escape(cell) for cell in row) + " |" for row in table.rows)
    if table.notes:
        out.append("")
        out.extend(f"- {note}" for note in table.notes)
    return "\n".join(out) + "\n"


FORMATTERS = {
    "text": render_text,
    "csv": render_csv,
    "markdown": render_markdown,
}


def render(table, name):
    try:
        formatter = FORMATTERS[name]
    except KeyError:
        raise UnknownFormat(name, list(FORMATTERS)) from None
    return formatter(table)
