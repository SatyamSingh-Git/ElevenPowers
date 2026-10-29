"""Amounts are whole pence everywhere; these turn them into text and back."""


def format_pence(pence):
    sign = "-" if pence < 0 else ""
    pounds, rest = divmod(abs(pence), 100)
    return f"{sign}{pounds}.{rest:02d}"


def parse_price(text):
    """'32.50' or '32' as 3250 pence. Negative amounts and fractions of a penny are refused."""
    text = text.strip()
    whole, _, fraction = text.partition(".")
    if not whole.isdigit() or (fraction and (not fraction.isdigit() or len(fraction) > 2)):
        raise ValueError(f"not a price: {text!r}")
    return int(whole) * 100 + int(fraction.ljust(2, "0"))
