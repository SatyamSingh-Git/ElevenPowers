from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from .discounts import allocate, discount_from_dict
from .items import ItemError, LineItem, line_from_dict
from .money import DEFAULT_ROUNDING, ROUNDING_MODES, currency_info, quantize
from .tax import line_tax, normalize_region

DEFAULT_CURRENCY = "USD"
MAX_LINE_ITEMS = 200
REQUIRED_FIELDS = ("number", "region", "lines")


class InvoiceError(ValueError):
    pass


@dataclass(frozen=True)
class Invoice:
    number: str
    region: str
    lines: tuple[LineItem, ...]
    currency: str = DEFAULT_CURRENCY
    issued: str | None = None
    discounts: tuple = ()
    rounding: str = DEFAULT_ROUNDING


@dataclass(frozen=True)
class LineTotal:
    item: LineItem
    gross: Decimal
    discount: Decimal
    net: Decimal
    tax: Decimal

    @property
    def total(self):
        return self.net + self.tax


@dataclass(frozen=True)
class Totals:
    currency: str
    lines: tuple[LineTotal, ...]
    subtotal: Decimal
    discount: Decimal
    tax: Decimal

    @property
    def net(self):
        return self.subtotal - self.discount

    @property
    def total(self):
        return self.net + self.tax


def _issue_date(value):
    if value is None:
        return None
    try:
        return date.fromisoformat(str(value)).isoformat()
    except ValueError:
        raise InvoiceError(f"issue date must be YYYY-MM-DD, not {value!r}") from None


def invoice_from_dict(data):
    for name in REQUIRED_FIELDS:
        if name not in data:
            raise InvoiceError(f"invoice missing field: {name}")
    number = str(data["number"]).strip()
    if not number:
        raise InvoiceError("invoice number must not be empty")
    currency = data.get("currency", DEFAULT_CURRENCY)
    currency_info(currency)
    rounding = data.get("rounding", DEFAULT_ROUNDING)
    if rounding not in ROUNDING_MODES:
        raise InvoiceError(f"unknown rounding mode: {rounding}")
    raw_lines = data["lines"]
    if not raw_lines:
        raise InvoiceError("an invoice needs at least one line item")
    if len(raw_lines) > MAX_LINE_ITEMS:
        raise InvoiceError(f"an invoice may have at most {MAX_LINE_ITEMS} line items")
    lines = []
    for n, raw in enumerate(raw_lines, 1):
        try:
            lines.append(line_from_dict(raw))
        except ItemError as error:
            raise ItemError(f"line {n}: {error}") from None
    return Invoice(
        number=number,
        region=normalize_region(data["region"]),
        lines=tuple(lines),
        currency=currency,
        issued=_issue_date(data.get("issued")),
        discounts=tuple(discount_from_dict(raw) for raw in data.get("discounts", ())),
        rounding=rounding,
    )


def compute(invoice):
    currency, rounding = invoice.currency, invoice.rounding
    grosses = [quantize(item.gross, currency, rounding) for item in invoice.lines]
    discounts = allocate(invoice.lines, grosses, invoice.discounts, currency, rounding)
    lines = []
    for item, gross, discount in zip(invoice.lines, grosses, discounts):
        net = gross - discount
        tax = line_tax(net, item.category, invoice.region, currency, rounding)
        lines.append(LineTotal(item, gross, discount, net, tax))
    return Totals(
        currency=currency,
        lines=tuple(lines),
        subtotal=sum(grosses, Decimal(0)),
        discount=sum(discounts, Decimal(0)),
        tax=sum((line.tax for line in lines), Decimal(0)),
    )
