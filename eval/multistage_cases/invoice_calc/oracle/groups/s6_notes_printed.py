from invoicekit import invoice_from_dict, render_text

NOTES = ("Payment is due within thirty days of the issue date. Please quote the invoice number "
         "with your payment so that we can match it quickly. Thank you for your business.")

INVOICE = {
    "number": "N-4", "issued": "2026-09-01", "region": "US-NY", "currency": "USD",
    "lines": [{"sku": "W-100", "description": "Widget", "quantity": 1, "unit_price": "5.00"}],
}


def contains_in_order(words, wanted):
    return any(words[n:n + len(wanted)] == wanted for n in range(len(words) - len(wanted) + 1))


def check(width):
    invoice = invoice_from_dict({**INVOICE, "notes": NOTES})
    lines = render_text(invoice, width=width).splitlines() if width else render_text(invoice).splitlines()
    total = max(n for n, line in enumerate(lines) if line.startswith("Total"))
    after = lines[total + 1:]
    assert contains_in_order(" ".join(after).split(), NOTES.split())
    assert all(len(line) <= (width or 64) for line in lines)
    assert sum(1 for line in after if line.strip()) >= 3


def test_notes_wrapped_under_the_totals():
    check(None)


def test_notes_follow_the_width():
    check(72)


def test_no_notes_means_nothing_after_the_total():
    lines = render_text(invoice_from_dict(INVOICE)).splitlines()
    total = max(n for n, line in enumerate(lines) if line.startswith("Total"))
    assert not any(line.strip() for line in lines[total + 1:])
