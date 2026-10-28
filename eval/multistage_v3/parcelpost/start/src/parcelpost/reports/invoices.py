"""Invoice documents, one text file per account and collection day."""
from ..core.money import format_amount
from .tables import render_table


def render_invoice(invoice):
    rows = [(charge.tracking_number, charge.service, format_amount(charge.pence))
            for charge in invoice.charges]
    summary = [
        ("", "Subtotal", format_amount(invoice.subtotal)),
        ("", f"VAT {invoice.vat_percent}%", format_amount(invoice.vat)),
        ("", "Total", format_amount(invoice.total)),
    ]
    heading = [
        f"Invoice {invoice.number}",
        f"Bill to {invoice.customer} ({invoice.account})",
        f"Collection day {invoice.day.isoformat()}",
        f"Payment due {invoice.due.isoformat()}",
        "",
    ]
    table = render_table(("Tracking number", "Service", "Amount"), rows + summary, right=("Amount",))
    return "\n".join(heading) + table + "\n"
