"""The receipt printed for a customer's order."""
from datetime import timedelta

from ..clock import format_time
from ..model.money import format_pence

WIDTH = 40


def render_receipt(order, performance, venue, settings):
    lines = [settings.theatre.center(WIDTH).rstrip(), "",
             f"Order {order.id}",
             f"{performance.title}, {_when(performance.starts)}", ""]
    for line in order.lines:
        label = f"{line.seat:<4} {venue.seat(line.seat).section:<10} {line.concession}"
        if line.refunded:
            label += " (refunded)"
        lines.append(_priced(label, line.price))
    lines.append(_priced("Booking fee", order.fee))
    lines.append(_priced(f"Total {settings.currency}", order.total))
    lines.append("")
    lines.append(f"Paid by {order.payment} on {_when(order.created)}")
    deadline = performance.starts - timedelta(hours=settings.refund_cutoff_hours)
    lines.append(f"Refundable until {_when(deadline)}")
    return "\n".join(lines)


def _priced(label, pence):
    amount = format_pence(pence)
    return f"{label:<{WIDTH - len(amount) - 1}} {amount}"


def _when(moment):
    return format_time(moment).replace("T", " ")


def render_tickets(order, performance, venue, theatre):
    """One ticket stub per seat still sold, separated by a cut line."""
    stubs = []
    for line in order.active_lines():
        seat = venue.seat(line.seat)
        stubs.append("\n".join([
            theatre,
            performance.title,
            _when(performance.starts),
            f"{seat.section}  row {seat.row}  seat {seat.number}",
            f"{line.concession}  {format_pence(line.price)}",
            f"order {order.id}",
        ]))
    return ("\n" + "-" * WIDTH + "\n").join(stubs)
