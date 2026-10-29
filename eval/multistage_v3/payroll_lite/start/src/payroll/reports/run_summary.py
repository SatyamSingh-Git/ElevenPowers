"""What `payroll run` and `payroll runs` print."""
from payroll.model.money import format_money
from payroll.model.payslip import TOTALS
from payroll.reports.formatting import table


def render_run(run):
    if not run.payslips:
        return f"Pay run {run.period.describe()}\n\nNobody was paid.\n"
    rows = [
        [slip.employee_id, slip.name] + [format_money(getattr(slip, name)) for name in TOTALS]
        for slip in run.payslips
    ]
    rows.append(["total", ""] + [format_money(run.total(name)) for name in TOTALS])
    header = ("employee", "name", *TOTALS)
    return f"Pay run {run.period.describe()}\n\n" + table(header, rows, numeric=range(2, len(header)))


def render_runs(runs):
    if not runs:
        return "No pay runs yet.\n"
    rows = [
        [run.period.id, run.period.pay_date.isoformat(), len(run.payslips), format_money(run.total("net"))]
        for run in runs
    ]
    return table(("period", "paid", "payslips", "net"), rows, numeric=(2, 3))
