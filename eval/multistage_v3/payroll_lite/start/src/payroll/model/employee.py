"""Employees and the allowances and deductions attached to them."""
from dataclasses import dataclass, field
from decimal import Decimal
import re

PAY_TYPES = ("hourly", "salaried")
EMPLOYEE_ID = re.compile(r"[A-Z][A-Z0-9]{1,9}")
BANK_ACCOUNT = re.compile(r"\d{2}-\d{4}-\d{7}-\d{2}")


@dataclass(frozen=True)
class Allowance:
    kind: str
    label: str
    amount: Decimal


@dataclass(frozen=True)
class Deduction:
    kind: str
    label: str
    params: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Employee:
    id: str
    name: str
    pay_type: str
    # An hourly rate for hourly staff, a yearly salary for salaried staff.
    rate: Decimal
    bank_account: str
    active: bool = True
    department: str = "General"
    allowances: tuple = ()
    deductions: tuple = ()

    @property
    def hourly(self):
        return self.pay_type == "hourly"

    def describe_rate(self):
        if self.hourly:
            return f"{self.rate:,.2f} per hour"
        return f"{self.rate:,.2f} per year"


def employee_problems(employee):
    """Everything wrong with an employee's own fields, as messages."""
    problems = []
    if not EMPLOYEE_ID.fullmatch(employee.id):
        problems.append(f"employee id {employee.id} must be a capital letter and 1 to 9 capitals or digits")
    if not employee.name.strip():
        problems.append(f"employee {employee.id} has no name")
    if employee.pay_type not in PAY_TYPES:
        problems.append(f"employee {employee.id}: pay type must be one of {', '.join(PAY_TYPES)}")
    if employee.rate <= 0:
        problems.append(f"employee {employee.id}: rate must be more than 0")
    if not BANK_ACCOUNT.fullmatch(employee.bank_account):
        problems.append(f"employee {employee.id}: bank account must look like 12-3456-7890123-00")
    return problems
