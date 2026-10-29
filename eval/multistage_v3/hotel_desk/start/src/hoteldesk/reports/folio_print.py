"""The folio as the guest sees it at check-out."""
from ..money import format_money
from .tables import amount_line

# Charges are grouped by code; anything not listed here prints under Extras.
SECTIONS = {"RM": "Accommodation", "TAX": "Taxes"}
SECTION_ORDER = ("Accommodation", "Taxes", "Extras")


def print_folio(hotel, reservation_id):
    reservation = hotel.reservation(reservation_id)
    folio = hotel.folio(reservation.id)
    lines = [
        hotel.name,
        f"Folio {reservation.id} - {reservation.guest}",
        f"Room {reservation.room} ({reservation.room_type})  "
        f"{reservation.arrival.isoformat()} to {reservation.departure.isoformat()}",
    ]
    grouped = {name: [] for name in SECTION_ORDER}
    for charge in folio.charges:
        grouped[SECTIONS.get(charge.code, "Extras")].append(charge)
    for name in SECTION_ORDER:
        if not grouped[name]:
            continue
        lines += ["", name]
        for charge in grouped[name]:
            lines.append(amount_line(f"  {charge.day.isoformat()}  {charge.description}",
                                     format_money(charge.amount)))
        lines.append(amount_line("  Subtotal", format_money(sum(charge.amount for charge in grouped[name]))))
    if folio.payments:
        lines += ["", "Payments"]
        for payment in folio.payments:
            lines.append(amount_line(f"  {payment.day.isoformat()}  {payment.method}",
                                     format_money(-payment.amount)))
    lines += ["", amount_line("Balance", format_money(folio.balance))]
    return "\n".join(lines)
