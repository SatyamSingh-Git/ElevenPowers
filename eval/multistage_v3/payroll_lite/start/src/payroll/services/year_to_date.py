"""Year-to-date totals for one employee, as printed at the foot of a payslip."""
from payroll.model.money import ZERO
from payroll.model.payslip import TOTALS
from payroll.services.payrun import list_runs


def year_to_date(data, run, employee_id):
    """Totals over the runs paid in the same calendar year as `run`, up to and including it."""
    paid = run.period.pay_date
    totals = dict.fromkeys(TOTALS, ZERO)
    for earlier in list_runs(data):
        if earlier.period.pay_date.year != paid.year or earlier.period.pay_date > paid:
            continue
        slip = earlier.payslip_for(employee_id)
        if slip is not None:
            for name in TOTALS:
                totals[name] += getattr(slip, name)
    return totals
