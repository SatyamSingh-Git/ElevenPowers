from dataclasses import dataclass
from decimal import Decimal

from .items import CATEGORIES
from .money import MoneyError, minor_units, quantize, to_decimal


class DiscountError(ValueError):
    pass


@dataclass(frozen=True)
class PercentOff:
    percent: Decimal
    category: str | None = None

    def applies_to(self, item):
        return self.category is None or self.category == item.category


@dataclass(frozen=True)
class AmountOff:
    amount: Decimal


def _decimal(data, name):
    if name not in data:
        raise DiscountError(f"discount missing field: {name}")
    try:
        return to_decimal(data[name])
    except MoneyError as error:
        raise DiscountError(f"discount {name}: {error}") from None


def discount_from_dict(data):
    kind = data.get("kind")
    if kind == "percent":
        percent = _decimal(data, "percent")
        if not 0 <= percent <= 100:
            raise DiscountError("discount percent must be between 0 and 100")
        category = data.get("category")
        if category is not None and category not in CATEGORIES:
            raise DiscountError(f"unknown category: {category}")
        return PercentOff(percent, category)
    if kind == "amount":
        amount = _decimal(data, "amount")
        if amount < 0:
            raise DiscountError("discount amount must not be negative")
        return AmountOff(amount)
    raise DiscountError(f"unknown discount kind: {kind}")


def allocate(items, grosses, discounts, currency, rounding):
    """Discount taken from each line.

    Percentages apply first, each to the gross of the lines it covers. Fixed
    amounts are then spread over what is left of each line, in proportion to
    it, and capped at what is left. No line loses more than its gross.
    """
    taken = [Decimal(0)] * len(items)
    for discount in discounts:
        if isinstance(discount, PercentOff):
            for n, item in enumerate(items):
                if discount.applies_to(item):
                    off = quantize(grosses[n] * discount.percent / 100, currency, rounding)
                    taken[n] = min(grosses[n], taken[n] + off)
    for discount in discounts:
        if isinstance(discount, AmountOff):
            left = [gross - off for gross, off in zip(grosses, taken)]
            for n, share in enumerate(_spread(discount.amount, left, currency)):
                taken[n] += share
    return taken


def _spread(amount, weights, currency):
    # Shares are counted in minor units so they add up to exactly the amount;
    # the units that proportional shares leave over go to the earliest lines.
    scale = Decimal(10) ** minor_units(currency)
    total = sum(weights)
    if not total:
        return [Decimal(0)] * len(weights)
    units = int(min(amount, total) * scale)
    shares = [int(units * weight / total) for weight in weights]
    leftover = units - sum(shares)
    for n, weight in enumerate(weights):
        if not leftover:
            break
        if shares[n] < weight * scale:
            shares[n] += 1
            leftover -= 1
    return [Decimal(share) / scale for share in shares]
