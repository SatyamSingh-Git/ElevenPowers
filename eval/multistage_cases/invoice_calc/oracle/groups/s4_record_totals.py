import pytest

from invoicekit import invoice_from_dict, read_records, to_record, write_records


def record(currency, price, category="standard", discounts=()):
    return to_record(invoice_from_dict({
        "number": "R-1", "issued": "2026-08-08", "region": "US-NY", "currency": currency,
        "lines": [{"sku": "A", "description": "a", "quantity": 2, "unit_price": price, "category": category}],
        "discounts": list(discounts),
    }))


def amounts(rec):
    return tuple(rec[name] for name in ("subtotal", "discount", "tax", "total"))


@pytest.mark.parametrize("currency, price, off, expected", [
    ("USD", "10.00", "4", (2000, 400, 142, 1742)),
    ("JPY", "411", "400", (822, 400, 37, 459)),
    ("KWD", "1.234", "0.4", (2468, 400, 184, 2252)),
])
def test_invoice_amounts_are_integer_minor_units(currency, price, off, expected):
    rec = record(currency, price, discounts=[{"kind": "amount", "amount": off}])
    assert amounts(rec) == expected
    assert all(type(value) is int for value in amounts(rec))


def test_integers_survive_a_file(tmp_path):
    rec = record("USD", "10.00")
    write_records(tmp_path / "r.jsonl", [rec])
    (back,) = read_records(tmp_path / "r.jsonl")
    assert amounts(back) == (2000, 0, 178, 2178)
    assert all(type(value) is int for value in amounts(back))
