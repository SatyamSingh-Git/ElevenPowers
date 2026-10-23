from decimal import Decimal, InvalidOperation

from invoicekit import compute, format_money, invoice_from_dict, render_text

INVOICE = {
    "number": "INV-2041", "issued": "2026-03-15", "region": "US-NY", "currency": "USD",
    "lines": [
        {"sku": "W-100", "description": "Widget", "quantity": 3, "unit_price": "19.99", "category": "standard"},
        {"sku": "BK-7", "description": "Field guide", "quantity": 2, "unit_price": "12.50", "category": "books"},
        {"sku": "SV-1", "description": "Installation", "quantity": 4, "unit_price": "45.00", "category": "services"},
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


def row_for(text, sku):
    return next(line for line in text.splitlines() if sku in line)


def test_totals():
    totals = compute(invoice_from_dict(INVOICE))
    assert totals.subtotal == Decimal("264.97")
    assert totals.tax == Decimal("7.54")
    assert totals.total == Decimal("272.51")


def test_heading():
    text = render_text(invoice_from_dict(INVOICE))
    for expected in ("INV-2041", "2026-03-15", "US-NY"):
        assert expected in text


def test_line_rows_show_quantity_and_amount():
    text = render_text(invoice_from_dict(INVOICE))
    for sku, quantity, amount in (("W-100", 3, "$59.97"), ("BK-7", 2, "$25.00"), ("SV-1", 4, "$180.00")):
        row = row_for(text, sku)
        assert Decimal(quantity) in numbers(row)
        assert amount in row


def test_totals_block():
    lines = render_text(invoice_from_dict(INVOICE)).splitlines()
    assert any(line.startswith("Subtotal") and line.rstrip().endswith("$264.97") for line in lines)
    assert any(line.startswith("Total") and line.rstrip().endswith("$272.51") for line in lines)
    assert any("8.875%" in line and line.rstrip().endswith("$7.54") for line in lines)


def test_width():
    invoice = invoice_from_dict(INVOICE)
    assert all(len(line) <= 64 for line in render_text(invoice).splitlines())
    wide = render_text(invoice, width=80).splitlines()
    assert all(len(line) <= 80 for line in wide)
    assert max(len(line) for line in wide) > 64


def test_yen_has_no_minor_units():
    invoice = invoice_from_dict({"number": "J-1", "issued": "2026-03-15", "region": "JP", "currency": "JPY",
                                 "lines": [{"sku": "T-1", "description": "Tea", "quantity": 3, "unit_price": "411",
                                            "category": "food"}]})
    lines = render_text(invoice).splitlines()
    assert "¥1,233" in row_for("\n".join(lines), "T-1")
    assert any(line.startswith("Total") and line.rstrip().endswith("¥1,332") for line in lines)


def test_format_money():
    assert format_money(Decimal("1234.5"), "USD") == "$1,234.50"
    assert format_money(Decimal("1234.5"), "JPY") == "¥1,235"
    assert format_money(Decimal("1.2345"), "KWD") == "KD 1.235"
