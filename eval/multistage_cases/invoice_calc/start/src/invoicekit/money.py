from decimal import ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal, InvalidOperation

from ._generated import CURRENCIES

ROUNDING_MODES = {
    "half-up": ROUND_HALF_UP,
    "half-even": ROUND_HALF_EVEN,
    "down": ROUND_DOWN,
}
DEFAULT_ROUNDING = "half-up"


class MoneyError(ValueError):
    pass


def currency_info(code):
    try:
        return CURRENCIES[code]
    except KeyError:
        raise MoneyError(f"unknown currency: {code}") from None


def minor_units(code):
    return currency_info(code)[1]


def rounding_mode(name):
    try:
        return ROUNDING_MODES[name]
    except KeyError:
        raise MoneyError(f"unknown rounding mode: {name}") from None


def to_decimal(value):
    if isinstance(value, float):
        raise MoneyError("amounts must be strings or integers, not float")
    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, int) and not isinstance(value, bool):
        result = Decimal(value)
    elif isinstance(value, str):
        try:
            result = Decimal(value.strip())
        except InvalidOperation:
            raise MoneyError(f"not a number: {value!r}") from None
    else:
        raise MoneyError(f"not a number: {value!r}")
    if not result.is_finite():
        raise MoneyError(f"not a number: {value!r}")
    return result


def quantize(amount, currency, rounding=DEFAULT_ROUNDING):
    step = Decimal(1).scaleb(-minor_units(currency))
    return amount.quantize(step, rounding=rounding_mode(rounding))


def format_money(amount, currency):
    symbol, places = currency_info(currency)
    amount = quantize(amount, currency)
    sign = "-" if amount < 0 else ""
    return f"{sign}{symbol}{abs(amount):,.{places}f}"
