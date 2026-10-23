import json

from .invoice import compute
from .tax import rate_for


def to_record(invoice):
    """The invoice and its totals as a plain dict, ready for JSON."""
    totals = compute(invoice)
    return {
        "number": invoice.number,
        "issued": invoice.issued,
        "region": invoice.region,
        "currency": invoice.currency,
        "subtotal": str(totals.subtotal),
        "discount": str(totals.discount),
        "tax": str(totals.tax),
        "total": str(totals.total),
        "lines": [
            {
                "sku": line.item.sku,
                "description": line.item.description,
                "category": line.item.category,
                "quantity": line.item.quantity,
                "unit_price": str(line.item.unit_price),
                "rate": str(rate_for(line.item.category, invoice.region)),
                "discount": str(line.discount),
                "net": str(line.net),
                "tax": str(line.tax),
                "total": str(line.total),
            }
            for line in totals.lines
        ],
    }


def write_records(path, records):
    with open(path, "w", encoding="utf-8", newline="\n") as out:
        for record in records:
            out.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def read_records(path):
    records = []
    with open(path, encoding="utf-8") as source:
        for number, text in enumerate(source, 1):
            if not text.strip():
                continue
            try:
                records.append(json.loads(text))
            except json.JSONDecodeError:
                raise ValueError(f"{path}, line {number}: not a JSON record") from None
    return records
