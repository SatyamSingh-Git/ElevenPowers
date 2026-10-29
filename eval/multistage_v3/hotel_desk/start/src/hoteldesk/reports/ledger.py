"""The guest ledger: what every in-house guest owes, for the auditor's balance check."""
from ..money import format_money
from ..services import booking

COLUMNS = ("room", "reservation", "guest", "charged", "paid", "balance")


def ledger_rows(hotel, day):
    # The ledger is always as of now; the day is accepted so every report reads alike.
    rows = []
    for reservation in booking.staying(hotel):
        folio = hotel.folio(reservation.id)
        rows.append({
            "room": reservation.room,
            "reservation": reservation.id,
            "guest": reservation.guest,
            "charged": format_money(folio.charged),
            "paid": format_money(folio.paid),
            "balance": format_money(folio.balance),
        })
    return rows
