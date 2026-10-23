import json
from decimal import Decimal

from invoicekit import invoice_from_dict, read_records, render_ledger, summarize, to_record, write_records


def invoice(number, region, currency, lines, discounts=()):
    return invoice_from_dict({"number": number, "issued": "2026-04-02", "region": region, "currency": currency,
                              "lines": lines, "discounts": list(discounts)})


def records():
    return [
        to_record(invoice("A-1", "US-NY", "USD", [
            {"sku": "W-100", "description": "Widget", "quantity": 3, "unit_price": "19.99", "category": "standard"},
            {"sku": "SV-1", "description": "Installation", "quantity": 4, "unit_price": "45.00",
             "category": "services"},
        ], [{"kind": "amount", "amount": "30"}])),
        to_record(invoice("A-2", "US-NY", "USD", [
            {"sku": "BK-7", "description": "Field guide", "quantity": 2, "unit_price": "12.50", "category": "books"},
        ])),
        to_record(invoice("E-1", "DE", "EUR", [
            {"sku": "F-3", "description": "Coffee", "quantity": 5, "unit_price": "3.20", "category": "food"},
        ], [{"kind": "percent", "percent": "10"}])),
    ]


def test_records_survive_a_file(tmp_path):
    path = tmp_path / "records.jsonl"
    write_records(path, records())
    assert read_records(path) == records()
    assert [json.loads(line)["number"] for line in path.read_text(encoding="utf-8").splitlines() if line.strip()] \
        == ["A-1", "A-2", "E-1"]


def test_summarize(tmp_path):
    path = tmp_path / "records.jsonl"
    write_records(path, records())
    rows = summarize(read_records(path))
    assert [(row.region, row.currency, row.invoices) for row in rows] == [("DE", "EUR", 1), ("US-NY", "USD", 2)]
    de, us = rows
    assert (us.subtotal, us.discount, us.tax, us.total) == (
        Decimal("264.97"), Decimal("30.00"), Decimal("6.88"), Decimal("241.85"))
    assert (de.subtotal, de.discount, de.tax, de.total) == (
        Decimal("16.00"), Decimal("1.60"), Decimal("1.01"), Decimal("15.41"))


def test_ledger_text():
    text = render_ledger(summarize(records()))
    us = next(line for line in text.splitlines() if line.startswith("US-NY"))
    de = next(line for line in text.splitlines() if line.startswith("DE"))
    for expected in ("$264.97", "-$30.00", "$6.88", "$241.85"):
        assert expected in us
    for expected in ("€16.00", "-€1.60", "€1.01", "€15.41"):
        assert expected in de
