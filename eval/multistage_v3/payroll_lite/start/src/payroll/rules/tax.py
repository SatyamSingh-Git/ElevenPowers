"""Income tax per period: the period's gross is treated as if earned all year at that pace."""
from decimal import Decimal

from payroll._generated import TAX_BANDS
from payroll.model.money import ZERO, round_money


def annual_tax(income):
    tax, lower = Decimal(0), Decimal(0)
    for upper, rate in TAX_BANDS:
        if upper is None or income <= upper:
            tax += (income - lower) * rate
            break
        tax += (upper - lower) * rate
        lower = upper
    return tax


def period_tax(gross, periods_per_year):
    if gross <= 0:
        return ZERO
    return round_money(annual_tax(gross * periods_per_year) / periods_per_year)
