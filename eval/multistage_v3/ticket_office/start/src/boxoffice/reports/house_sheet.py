"""The house manager's sheet for one performance: numbers in, and who needs what."""
from collections import Counter

from .._generated import ACCESSIBILITY_CODES
from ..clock import format_time


def house_sheet(performance, venue, orders, customers):
    """Plain text for the house manager to print before the doors open.

    It counts the audience by section and concession, and lists every sold
    seat that carries an access code, so the ushers know where to help.
    """
    by_section = Counter()
    by_concession = Counter()
    access = []
    position = venue.seat_order()
    for order in sorted(orders.values(), key=lambda order: order.id):
        if order.performance != performance.code:
            continue
        name = customers[order.customer].name if order.customer in customers else "-"
        for line in order.active_lines():
            seat = venue.seat(line.seat)
            by_section[seat.section] += 1
            by_concession[line.concession] += 1
            for flag in sorted(seat.flags):
                access.append((position[seat.id], seat.id, ACCESSIBILITY_CODES[flag], name))
    lines = [f"{performance.title}, {format_time(performance.starts).replace('T', ' ')}",
             f"Audience: {sum(by_section.values())} of {venue.capacity}", ""]
    for section in venue.sections:
        lines.append(f"  {section.name:<12} {by_section[section.name]:>4} of {section.capacity}")
    lines.append("")
    for name, count in sorted(by_concession.items()):
        lines.append(f"  {name:<12} {count:>4}")
    lines.append("")
    if access:
        lines.append("Access seats sold:")
        for _, seat_id, need, name in sorted(access):
            lines.append(f"  {seat_id:<5} {need:<18} {name}")
    else:
        lines.append("No access seats sold.")
    return "\n".join(lines)
