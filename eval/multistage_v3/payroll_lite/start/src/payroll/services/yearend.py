"""Year-end totals per employee, from the pay runs paid during the year."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
import json

from payroll.model.money import ZERO


@dataclass
class YearTotals:
    employee_id: str
    name: str
    gross: Decimal = ZERO
    tax: Decimal = ZERO
    deductions: Decimal = ZERO
    net: Decimal = ZERO


def year_totals(data, year):
    """One row per employee paid in `year`, counting a run by its pay date, not its period."""
    totals = {}
    for path in sorted(data.runs.glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        if date.fromisoformat(document["pay_date"]).year != year:
            continue
        for slip in document["payslips"]:
            row = totals.setdefault(slip["employee_id"], YearTotals(slip["employee_id"], slip["name"]))
            # Runs are read in period order, so the name kept is the latest one paid.
            row.name = slip["name"]
            row.gross += Decimal(slip["gross"])
            row.tax += Decimal(slip["tax"])
            row.deductions += Decimal(slip["deductions"])
            row.net += Decimal(slip["net"])
    return [totals[employee_id] for employee_id in sorted(totals)]
