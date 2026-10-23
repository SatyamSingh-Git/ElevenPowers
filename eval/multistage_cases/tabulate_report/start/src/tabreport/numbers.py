"""Reading amounts out of CSV cells and printing numbers back."""
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from ._generated import CURRENCIES
from .errors import ReportError

# Longest first, so "CA$" is not taken for a bare "C" followed by junk.
_SYMBOLS = sorted({symbol.strip() for symbol, _ in CURRENCIES.values()}, key=len, reverse=True)


def parse_amount(text, thousands=","):
    """The Decimal in a cell such as ``1,234.50``, ``-$12``, ``(7.25)`` or ``CHF 3``.

    Parentheses mean a negative amount, as accounting exports write them.
    """
    cleaned = text.strip()
    sign = 1
    if cleaned.startswith("(") and cleaned.endswith(")"):
        sign, cleaned = -1, cleaned[1:-1].strip()
    if cleaned[:1] in ("-", "+"):
        if cleaned[0] == "-":
            sign = -sign
        cleaned = cleaned[1:].lstrip()
    for symbol in _SYMBOLS:
        if cleaned.startswith(symbol):
            cleaned = cleaned[len(symbol):].lstrip()
            break
    if thousands:
        cleaned = cleaned.replace(thousands, "")
    try:
        value = Decimal(cleaned)
    except InvalidOperation:
        raise ReportError(f"not a number: {text!r}") from None
    if not value.is_finite():
        raise ReportError(f"not a number: {text!r}")
    return sign * value


def format_number(value, places=2, thousands=","):
    """``value`` rounded half up to ``places`` decimals, digits grouped by ``thousands``."""
    rounded = Decimal(value).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    whole, _, fraction = f"{abs(rounded):f}".partition(".")
    if thousands:
        whole = _group(whole, thousands)
    text = f"{whole}.{fraction}" if fraction else whole
    return f"-{text}" if rounded < 0 else text


def _group(digits, separator):
    head = len(digits) % 3 or 3
    parts = [digits[:head]] + [digits[i:i + 3] for i in range(head, len(digits), 3)]
    return separator.join(parts)
