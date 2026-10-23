from decimal import Decimal, InvalidOperation

from invoicekit import invoice_from_dict, read_records, render_ledger, render_text, summarize, to_record, write_records

INVOICE = {
    "number": "H-7", "issued": "2026-05-04", "region": "US-NY", "currency": "USD",
    "lines": [
        {"sku": "SV-2", "description": "Consulting", "quantity": "1.5", "unit_price": "80.00", "category": "services"},
        {"sku": "C-1", "description": "Cloud credits", "quantity": "0.25", "unit_price": "100.00"},
        {"sku": "W-100", "description": "Widget", "quantity": 2, "unit_price": "19.99"},
    ],
}


def numbers(row):
    found = []
    for token in row.split():
        try:
            found.append(Decimal(token))
        except InvalidOperation:
            pass
    return found


def test_printed_invoice_shows_fractional_quantities():
    text = render_text(invoice_from_dict(INVOICE))
    rows = {sku: next(line for line in text.splitlines() if sku in line) for sku in ("SV-2", "C-1", "W-100")}
    assert Decimal("1.5") in numbers(rows["SV-2"]) and "$120.00" in rows["SV-2"]
    assert Decimal("0.25") in numbers(rows["C-1"]) and "$25.00" in rows["C-1"]
    assert Decimal(2) in numbers(rows["W-100"]) and "$39.98" in rows["W-100"]
    assert any(line.startswith("Total") and line.rstrip().endswith("$190.75") for line in text.splitlines())


def test_fractional_quantities_reach_the_ledger(tmp_path):
    path = tmp_path / "records.jsonl"
    write_records(path, [to_record(invoice_from_dict(INVOICE))])
    (row,) = summarize(read_records(path))
    assert (row.invoices, row.subtotal, row.tax, row.total) == (1, Decimal("184.98"), Decimal("5.77"),
                                                                Decimal("190.75"))
    assert "$190.75" in render_ledger([row])
