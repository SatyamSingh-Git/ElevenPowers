"""What a pay run produces: payslips made of lines, and the run that holds them."""
from dataclasses import dataclass
from decimal import Decimal

from payroll.model.money import total
from payroll.model.period import PayPeriod

TOTALS = ("gross", "tax", "deductions", "net")


@dataclass(frozen=True)
class Line:
    kind: str
    label: str
    amount: Decimal
    hours: Decimal | None = None
    rate: Decimal | None = None


@dataclass(frozen=True)
class Payslip:
    employee_id: str
    name: str
    lines: tuple
    gross: Decimal
    tax: Decimal
    deductions: Decimal
    net: Decimal


@dataclass(frozen=True)
class PayRun:
    period: PayPeriod
    payslips: tuple

    def total(self, name):
        return total(getattr(slip, name) for slip in self.payslips)

    def payslip_for(self, employee_id):
        for slip in self.payslips:
            if slip.employee_id == employee_id:
                return slip
        return None
