"""`payroll costs`: what a pay run's gross pay came to in each department."""
from dataclasses import dataclass, field
from decimal import Decimal

from payroll.model.money import ZERO, format_money, total
from payroll.reports.formatting import table

UNKNOWN_DEPARTMENT = "(not on payroll)"


@dataclass
class DepartmentCost:
    department: str
    people: set = field(default_factory=set)
    allowances: Decimal = ZERO
    gross: Decimal = ZERO

    @property
    def wages(self):
        return self.gross - self.allowances


def department_costs(run, employees):
    """Costs by department; people who have since been removed from the payroll are grouped apart."""
    costs = {}
    for slip in run.payslips:
        employee = employees.get(slip.employee_id)
        department = employee.department if employee else UNKNOWN_DEPARTMENT
        cost = costs.setdefault(department, DepartmentCost(department))
        cost.people.add(slip.employee_id)
        cost.allowances += total(line.amount for line in slip.lines if line.kind == "allowance")
        cost.gross += slip.gross
    return [costs[name] for name in sorted(costs)]


def render_costs(run, costs):
    if not costs:
        return f"Nobody was paid in {run.period.id}.\n"
    rows = [
        [cost.department, len(cost.people), format_money(cost.wages), format_money(cost.allowances),
         format_money(cost.gross)]
        for cost in costs
    ]
    rows.append([
        "total",
        sum(len(cost.people) for cost in costs),
        format_money(total(cost.wages for cost in costs)),
        format_money(total(cost.allowances for cost in costs)),
        format_money(total(cost.gross for cost in costs)),
    ])
    header = ("department", "people", "wages", "allowances", "gross")
    return f"Costs for {run.period.describe()}\n\n" + table(header, rows, numeric=(1, 2, 3, 4))
