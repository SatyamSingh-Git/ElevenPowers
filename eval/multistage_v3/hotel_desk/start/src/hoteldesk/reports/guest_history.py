"""A guest's profile and stays, for the desk to read before a repeat guest arrives."""
from ..money import format_money
from ..services import guests
from .tables import table


def guest_card(hotel, name):
    profile = hotel.guest(name)
    summary = guests.history(hotel, name)
    lines = [
        f"{profile.name}{'  (VIP)' if profile.vip else ''}",
        f"email: {profile.email or '-'}  phone: {profile.phone or '-'}",
    ]
    if profile.notes:
        lines.append(f"notes: {profile.notes}")
    lines.append(f"{summary['stays']} stays, {summary['nights']} nights, "
                 f"{format_money(summary['room_revenue'])} room revenue")
    reservations = guests.stays(hotel, name)
    if reservations:
        lines.append(table(("reservation", "arrival", "nights", "type", "status"),
                           [(r.id, r.arrival.isoformat(), r.nights, r.room_type, r.status) for r in reservations]))
    return "\n".join(lines)
