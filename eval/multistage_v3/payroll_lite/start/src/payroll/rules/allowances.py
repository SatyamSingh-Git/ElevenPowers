"""Allowances paid on top of wages, chosen by each allowance's `kind`."""
from payroll.errors import PayrollError
from payroll.model.money import round_money
from payroll.model.payslip import Line


def _fixed(allowance, hours):
    return Line("allowance", allowance.label, allowance.amount)


def _per_shift(allowance, hours):
    if not hours.shifts:
        return None
    amount = round_money(allowance.amount * hours.shifts)
    return Line("allowance", f"{allowance.label} x {hours.shifts}", amount, rate=allowance.amount)


ALLOWANCES = {
    "fixed": _fixed,
    "per_shift": _per_shift,
}


def check_kind(kind):
    if kind not in ALLOWANCES:
        raise PayrollError(f"unknown allowance kind {kind}; expected one of {', '.join(ALLOWANCES)}")


def allowance_lines(allowances, hours):
    lines = []
    for allowance in allowances:
        line = ALLOWANCES[allowance.kind](allowance, hours)
        if line is not None:
            lines.append(line)
    return lines
