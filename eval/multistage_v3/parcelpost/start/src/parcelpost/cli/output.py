"""What the command line prints for quotes, shipments, tracking and invoices."""
from dataclasses import fields

from ..core.clock import format_timestamp
from ..core.money import format_amount
from ..core.units import format_kg
from ..reports.tables import render_table

LINE_TITLES = {
    "base": "Postage",
    "residential": "Residential delivery",
    "signature": "Signature on delivery",
    "oversize": "Oversize parcel",
    "insurance": "Declared value cover",
    "fuel": "Fuel levy",
}


def quote_text(quote, name, expected):
    rows = [(LINE_TITLES[line.code], format_amount(line.pence)) for line in quote.lines]
    rows.append(("Total", format_amount(quote.total)))
    heading = (f"{name}: zone {quote.zone}, billable weight {format_kg(quote.billable_grams)} kg, "
               f"expected {expected.isoformat()}")
    return heading + "\n" + render_table(("Charge", "Amount"), rows, right=("Amount",))


def shipments_table(shipments):
    rows = [(shipment.tracking_number, shipment.account, shipment.service,
             shipment.ship_date.isoformat(), shipment.status, format_amount(shipment.total))
            for shipment in shipments]
    return render_table(("Tracking number", "Account", "Service", "Ships", "Status", "Charge"),
                        rows, right=("Charge",))


def tracking_text(tracking, today):
    shipment = tracking.shipment
    lines = [
        f"{shipment.tracking_number}  {tracking.status}" + ("  LATE" if tracking.late_on(today) else ""),
        f"Ships {shipment.ship_date.isoformat()}, expected {shipment.expected_delivery.isoformat()}",
    ]
    if tracking.events:
        lines.append(render_table(("Time", "Scan", "Depot"),
                                  [(format_timestamp(event.at), event.code, event.depot)
                                   for event in tracking.events]))
    else:
        lines.append("No scans yet.")
    return "\n".join(lines)


def invoices_table(invoices):
    rows = [(invoice.number, invoice.account, len(invoice.charges), format_amount(invoice.subtotal),
             format_amount(invoice.vat), format_amount(invoice.total)) for invoice in invoices]
    return render_table(("Invoice", "Account", "Shipments", "Subtotal", "VAT", "Total"), rows,
                        right=("Shipments", "Subtotal", "VAT", "Total"))


def reconciliation_text(result):
    heading = f"{result.day.isoformat()}: {result.matched} shipments match the carrier's invoice"
    if result.balanced:
        return heading
    rows = [(difference.tracking_number, difference.problem,
             "" if difference.ours is None else format_amount(difference.ours),
             "" if difference.theirs is None else format_amount(difference.theirs))
            for difference in result.differences]
    table = render_table(("Tracking number", "Problem", "Ours", "Carrier"), rows,
                         right=("Ours", "Carrier"))
    return f"{heading}, {len(rows)} do not\n{table}"


def claims_table(claims):
    rows = [(claim.number, claim.tracking_number, claim.reason, claim.raised_on, format_amount(claim.pence))
            for claim in claims]
    return render_table(("Claim", "Tracking number", "Reason", "Raised", "Amount"), rows, right=("Amount",))


def accounts_table(accounts):
    rows = [(account.code, account.name, account.email, account.payment_days) for account in accounts]
    return render_table(("Account", "Name", "Email", "Payment days"), rows, right=("Payment days",))


def settings_text(settings):
    rows = []
    for field in fields(settings):
        value = getattr(settings, field.name)
        rows.append((field.name, value.strftime("%H:%M") if field.name == "cutoff" else str(value)))
    return render_table(("Setting", "Value"), rows)


def zones_text(areas_by_zone):
    return "\n".join(f"zone {zone}: {' '.join(areas)}" for zone, areas in areas_by_zone.items())
