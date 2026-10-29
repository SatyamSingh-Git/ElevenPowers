"""The year-end summary: a table for people or CSV for the accountant."""
import csv
import io

from payroll.model.money import format_money, plain_money, total
from payroll.reports.formatting import table

COLUMNS = ("employee_id", "name", "gross", "tax", "deductions", "net")
AMOUNTS = ("gross", "tax", "deductions", "net")


def render_text(year, rows):
    if not rows:
        return f"No pay runs were paid in {year}.\n"
    body = [[row.employee_id, row.name] + [format_money(getattr(row, name)) for name in AMOUNTS] for row in rows]
    body.append(["total", ""] + [format_money(total(getattr(row, name) for row in rows)) for name in AMOUNTS])
    return f"Year-end summary {year}\n\n" + table(COLUMNS, body, numeric=range(2, len(COLUMNS)))


def render_csv(year, rows):
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(COLUMNS)
    for row in rows:
        writer.writerow([row.employee_id, row.name] + [plain_money(getattr(row, name)) for name in AMOUNTS])
    return out.getvalue()


FORMATS = {
    "text": render_text,
    "csv": render_csv,
}
