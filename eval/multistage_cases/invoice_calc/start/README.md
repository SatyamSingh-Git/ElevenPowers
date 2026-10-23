# invoicekit

Invoice arithmetic with the standard library only: line items, percent and
fixed discounts, tax by region and category, rounding, currency formatting,
a printable text invoice, JSON lines export and a ledger summary.

```python
from invoicekit import invoice_from_dict, render_text

invoice = invoice_from_dict({
    "number": "INV-2041", "issued": "2026-03-15", "region": "US-NY",
    "lines": [{"sku": "W-100", "description": "Widget", "quantity": 3, "unit_price": "19.99"}],
})
print(render_text(invoice))
```

From the shell:

```
python -m invoicekit render invoice.json --width 72
python -m invoicekit export records.jsonl a.json b.json
python -m invoicekit ledger records.jsonl
```

Run the tests with `python -m pytest`. See `docs/reference.md` for fields,
defaults, rates and error messages.
