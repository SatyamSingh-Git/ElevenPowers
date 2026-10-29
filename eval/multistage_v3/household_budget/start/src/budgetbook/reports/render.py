"""Writing a report as text, CSV or Markdown.

A report is a title and a list of sections, each a small table. Amount cells
hold integer cents and are formatted by the renderer: grouped thousands for
people, plain decimals for CSV.
"""
import csv
from dataclasses import dataclass, field
import io

from ..errors import ValidationError
from ..model.money import decimal_text, format_amount


@dataclass(frozen=True)
class Section:
    title: str
    columns: tuple
    rows: list
    amounts: tuple = field(default=())


@dataclass(frozen=True)
class Report:
    title: str
    sections: list


def _cells(section, row, money):
    return [money(value) if column in section.amounts else str(value)
            for column, value in zip(section.columns, row)]


def render_text(report):
    lines = [report.title, "=" * len(report.title)]
    for section in report.sections:
        lines += ["", section.title]
        if not section.rows:
            lines.append("  (none)")
            continue
        table = [list(section.columns)] + [_cells(section, row, format_amount) for row in section.rows]
        widths = [max(len(row[i]) for row in table) for i in range(len(section.columns))]
        for row in table:
            cells = [cell.rjust(width) if column in section.amounts else cell.ljust(width)
                     for cell, width, column in zip(row, widths, section.columns)]
            lines.append("  " + "  ".join(cells).rstrip())
    return "\n".join(lines) + "\n"


def render_csv(report):
    """One header row per section; every row starts with its section's title."""
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    for section in report.sections:
        writer.writerow(["section", *section.columns])
        for row in section.rows:
            writer.writerow([section.title, *_cells(section, row, decimal_text)])
    return out.getvalue()


def render_markdown(report):
    lines = [f"# {report.title}"]
    for section in report.sections:
        lines += ["", f"## {section.title}", ""]
        if not section.rows:
            lines.append("_None._")
            continue
        lines.append("| " + " | ".join(section.columns) + " |")
        lines.append("|" + "|".join("---:" if column in section.amounts else "---"
                                    for column in section.columns) + "|")
        for row in section.rows:
            cells = [cell.replace("|", "\\|") for cell in _cells(section, row, format_amount)]
            lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


RENDERERS = {
    "text": render_text,
    "csv": render_csv,
    "markdown": render_markdown,
}


def render(report, format_name):
    try:
        renderer = RENDERERS[format_name]
    except KeyError:
        raise ValidationError(f"unknown report format: {format_name}") from None
    return renderer(report)
