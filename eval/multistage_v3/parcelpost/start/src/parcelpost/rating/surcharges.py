"""Surcharges on top of base postage.

Each rule is registered under the code that appears on quote lines and in the
manifest, and returns the amount in pence, or 0 when it does not apply. Rules
run in the order they are registered here.
"""
from dataclasses import dataclass
from decimal import Decimal

from ..core.charges import Line
from ..core.money import percent_of

RESIDENTIAL_PENCE = 350
SIGNATURE_PENCE = 200
OVERSIZE_PENCE = 1200
HEAVY_GRAMS = 25_000
LONG_CM = 100
INSURED_ABOVE_PENCE = 10_000
INSURANCE_PERCENT = Decimal("1.5")
INSURANCE_MINIMUM_PENCE = 200

_RULES = {}


@dataclass(frozen=True)
class Context:
    parcel: object
    service: str
    zone: int
    residential: bool
    signature: bool


def rule(code):
    def register(function):
        _RULES[code] = function
        return function
    return register


@rule("residential")
def _residential_delivery(context):
    return RESIDENTIAL_PENCE if context.residential else 0


@rule("signature")
def _signature_on_delivery(context):
    return SIGNATURE_PENCE if context.signature else 0


@rule("oversize")
def _large_parcel(context):
    parcel = context.parcel
    if parcel.weight_grams > HEAVY_GRAMS or parcel.longest_side > LONG_CM:
        return OVERSIZE_PENCE
    return 0


@rule("insurance")
def _declared_value_cover(context):
    declared = context.parcel.declared_pence
    if declared <= INSURED_ABOVE_PENCE:
        return 0
    return max(percent_of(declared, INSURANCE_PERCENT), INSURANCE_MINIMUM_PENCE)


def codes():
    return list(_RULES)


def applicable(context):
    lines = []
    for code, charge in _RULES.items():
        amount = charge(context)
        if amount:
            lines.append(Line(code, amount))
    return lines
