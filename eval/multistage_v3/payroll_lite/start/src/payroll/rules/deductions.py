"""Deductions taken from gross pay after tax, chosen by each deduction's `kind`."""
from dataclasses import dataclass

from payroll.errors import PayrollError
from payroll.model.money import parse_money, parse_rate, percent_of
from payroll.model.payslip import Line


@dataclass(frozen=True)
class DeductionRule:
    # parameter name -> parser for the text stored in employees.json
    params: dict
    # (parsed params, gross pay) -> amount to deduct
    amount: object


def _fixed(params, gross):
    return params["amount"]


def _percent(params, gross):
    return percent_of(gross, params["rate"])


DEDUCTIONS = {
    "fixed": DeductionRule({"amount": parse_money}, _fixed),
    "percent": DeductionRule({"rate": parse_rate}, _percent),
}


def parse_params(kind, values):
    """The parameters a deduction of `kind` needs, parsed from the text given for them."""
    rule = DEDUCTIONS.get(kind)
    if rule is None:
        raise PayrollError(f"unknown deduction kind {kind}; expected one of {', '.join(DEDUCTIONS)}")
    params = {}
    for name, parse in rule.params.items():
        if values.get(name) is None:
            raise PayrollError(f"a {kind} deduction needs {name}")
        params[name] = parse(values[name], name)
    return params


def deduction_lines(deductions, gross):
    lines = []
    for deduction in deductions:
        amount = DEDUCTIONS[deduction.kind].amount(deduction.params, gross)
        if amount > 0:
            lines.append(Line("deduction", deduction.label, amount))
    return lines
