from decimal import Decimal

from .invoice import compute
from .money import format_money
from .tax import format_rate, rate_for

DEFAULT_WIDTH = 64
MIN_WIDTH = 56
SKU_COLUMN = 10
QUANTITY_COLUMN = 6
AMOUNT_COLUMN = 13


def _clip(text, size):
    return text if len(text) <= size else text[: size - 3] + "..."


def _row(label, amount, width):
    return f"{label:<{width - AMOUNT_COLUMN}}{amount:>{AMOUNT_COLUMN}}"


def _tax_summary(invoice, totals):
    """(rate, taxed amount, tax) for each rate on the invoice, highest rate first."""
    by_rate = {}
    for line in totals.lines:
        rate = rate_for(line.item.category, invoice.region)
        base, tax = by_rate.get(rate, (Decimal(0), Decimal(0)))
        by_rate[rate] = (base + line.net, tax + line.tax)
    return [(rate, base, tax) for rate, (base, tax) in sorted(by_rate.items(), reverse=True)]


def render_text(invoice, width=DEFAULT_WIDTH):
    if width < MIN_WIDTH:
        raise ValueError(f"width must be at least {MIN_WIDTH}")
    totals = compute(invoice)

    def money(amount):
        return format_money(amount, invoice.currency)

    description_column = width - SKU_COLUMN - QUANTITY_COLUMN - 2 * AMOUNT_COLUMN
    rule = "-" * width
    out = [
        f"INVOICE {invoice.number}",
        f"Issued: {invoice.issued or '-'}   Region: {invoice.region}   Currency: {invoice.currency}",
        rule,
        f"{'SKU':<{SKU_COLUMN}}{'Description':<{description_column}}{'Qty':>{QUANTITY_COLUMN}}"
        f"{'Unit':>{AMOUNT_COLUMN}}{'Amount':>{AMOUNT_COLUMN}}",
    ]
    for line in totals.lines:
        item = line.item
        out.append(
            f"{_clip(item.sku, SKU_COLUMN - 1):<{SKU_COLUMN}}"
            f"{_clip(item.description, description_column - 1):<{description_column}}"
            f"{item.quantity:>{QUANTITY_COLUMN}d}"
            f"{money(item.unit_price):>{AMOUNT_COLUMN}}{money(line.gross):>{AMOUNT_COLUMN}}"
        )
        if line.discount:
            out.append(_row("    discount", money(-line.discount), width))
    out.append(rule)
    out.append(_row("Subtotal", money(totals.subtotal), width))
    if totals.discount:
        out.append(_row("Discount", money(-totals.discount), width))
    for rate, base, tax in _tax_summary(invoice, totals):
        out.append(_row(f"Tax {format_rate(rate)} on {money(base)}", money(tax), width))
    out.append(_row("Total", money(totals.total), width))
    return "\n".join(out) + "\n"
