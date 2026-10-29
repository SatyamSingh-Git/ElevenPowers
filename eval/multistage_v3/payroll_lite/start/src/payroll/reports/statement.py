"""Earnings statements: one page per employee with what they were paid in a year."""
from payroll.model.money import format_money

LINES = (("Gross pay", "gross"), ("Tax", "tax"), ("Deductions", "deductions"), ("Net pay", "net"))


def render_statement(company, year, row):
    out = [
        company,
        f"Earnings statement for {year}",
        f"{row.name} ({row.employee_id})",
        "",
    ]
    out += [f"{label:<16}{format_money(getattr(row, name)):>14}" for label, name in LINES]
    return "\n".join(out) + "\n"


def statement_name(year, row):
    return f"{row.employee_id}-{year}.txt"
