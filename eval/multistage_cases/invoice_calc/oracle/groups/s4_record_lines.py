from invoicekit import invoice_from_dict, to_record


def test_line_amounts_are_integer_minor_units():
    rec = to_record(invoice_from_dict({
        "number": "R-2", "issued": "2026-08-08", "region": "US-NY", "currency": "USD",
        "lines": [
            {"sku": "A", "description": "a", "quantity": 1, "unit_price": "10.00", "category": "standard"},
            {"sku": "B", "description": "b", "quantity": 1, "unit_price": "10.00", "category": "food"},
            {"sku": "C", "description": "c", "quantity": 1, "unit_price": "10.00", "category": "books"},
        ],
        "discounts": [{"kind": "amount", "amount": "10"}],
    }))
    lines = [(line["discount"], line["net"], line["tax"], line["total"]) for line in rec["lines"]]
    assert lines == [(334, 666, 59, 725), (333, 667, 0, 667), (333, 667, 59, 726)]
    assert all(type(value) is int for line in lines for value in line)


def test_yen_lines_are_whole_yen():
    rec = to_record(invoice_from_dict({
        "number": "R-3", "issued": "2026-08-08", "region": "JP", "currency": "JPY",
        "lines": [{"sku": "A", "description": "a", "quantity": 3, "unit_price": "411", "category": "food"}],
    }))
    (line,) = rec["lines"]
    assert (line["discount"], line["net"], line["tax"], line["total"]) == (0, 1233, 99, 1332)
