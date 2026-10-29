"""The payslip an employee receives for one pay run."""
from collections import defaultdict

from payroll.model.money import format_money

# Which heading each kind of payslip line is printed under.
SECTIONS = {
    "basic": "Earnings",
    "overtime": "Earnings",
    "holiday": "Earnings",
    "sick": "Earnings",
    "allowance": "Earnings",
    "deduction": "Deductions",
}


def render_payslip(company, period, slip, year_to_date=None):
    sections = defaultdict(list)
    for line in slip.lines:
        sections[SECTIONS[line.kind]].append(line)
    out = [
        company,
        f"Payslip for {slip.name} ({slip.employee_id})",
        f"Period {period.describe()}",
        "",
    ]
    out += _section("Earnings", sections)
    out.append(_row("Gross pay", slip.gross))
    out.append(_row("Tax", slip.tax))
    out += _section("Deductions", sections)
    out.append(_row("Net pay", slip.net))
    if year_to_date:
        sums = ", ".join(f"{name} {format_money(amount)}" for name, amount in year_to_date.items())
        out += ["", f"Year to date: {sums}"]
    return "\n".join(out) + "\n"


def _section(heading, sections):
    if not sections[heading]:
        return []
    return [heading] + [_row("  " + line.label, line.amount, _detail(line)) for line in sections[heading]]


def _detail(line):
    if line.hours is None:
        return ""
    return f"{line.hours:.2f} h x {line.rate:.2f}"


def _row(label, amount, detail=""):
    return f"{label:<26}{detail:<20}{format_money(amount):>12}"
