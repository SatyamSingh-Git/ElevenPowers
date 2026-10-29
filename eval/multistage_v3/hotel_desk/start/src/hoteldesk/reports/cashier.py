"""The cashier's report: payments taken on a day, by method, for the cash-up."""
from ..money import format_money
from ..services.billing import PAYMENT_METHODS
from .tables import amount_line, table

COLUMNS = ("reservation", "guest", "method", "amount")


def payments_on(hotel, day):
    """(reservation, guest, payment) for every payment dated `day`, by reservation."""
    taken = []
    for reservation_id in sorted(hotel.folios):
        guest = hotel.reservation(reservation_id).guest
        for payment in hotel.folios[reservation_id].payments:
            if payment.day == day:
                taken.append((reservation_id, guest, payment))
    return taken


def cashier_rows(hotel, day):
    return [
        {"reservation": reservation_id, "guest": guest, "method": payment.method,
         "amount": format_money(payment.amount)}
        for reservation_id, guest, payment in payments_on(hotel, day)
    ]


def cash_up_text(hotel, day):
    taken = payments_on(hotel, day)
    by_method = dict.fromkeys(PAYMENT_METHODS, 0)
    for _, _, payment in taken:
        by_method[payment.method] += payment.amount
    lines = [f"Cash-up for {day.isoformat()}"]
    if taken:
        lines.append(table(COLUMNS, [[row[column] for column in COLUMNS] for row in cashier_rows(hotel, day)],
                           right=("amount",)))
    lines.append("")
    for method, amount in by_method.items():
        lines.append(amount_line(method.capitalize(), format_money(amount), 32))
    lines.append(amount_line("Total", format_money(sum(by_method.values())), 32))
    return "\n".join(lines)
