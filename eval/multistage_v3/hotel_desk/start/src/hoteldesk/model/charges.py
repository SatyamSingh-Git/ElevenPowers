"""Charge codes the desk posts to folios, and the tax each one carries."""
from dataclasses import dataclass

from .._generated import TAX_RATES
from ..errors import ValidationError


@dataclass(frozen=True)
class ChargeCode:
    code: str
    description: str
    tax_category: str


ROOM = "RM"
TAX = "TAX"
LATE_CHECKOUT = "LCO"

CHARGE_CODES = {
    charge.code: charge
    for charge in (
        ChargeCode(ROOM, "Room", "lodging"),
        ChargeCode(TAX, "Tax", "exempt"),
        ChargeCode("FB", "Food and beverage", "sales"),
        ChargeCode("MB", "Minibar", "sales"),
        ChargeCode("PK", "Parking", "sales"),
        ChargeCode("PH", "Telephone", "exempt"),
        ChargeCode(LATE_CHECKOUT, "Late check-out", "lodging"),
    )
}


def lookup(code):
    try:
        return CHARGE_CODES[code.upper()]
    except KeyError:
        raise ValidationError(f"Unknown charge code: {code}") from None


def tax_rate(charge_code):
    return TAX_RATES[charge_code.tax_category]
