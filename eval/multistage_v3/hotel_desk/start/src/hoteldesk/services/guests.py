"""Guest profiles and what the hotel knows of a guest's past stays."""
from ..errors import ValidationError
from ..model.guests import Guest
from ..model.reservations import CHECKED_OUT, IN_HOUSE


def save_profile(hotel, name, *, email=None, phone=None, vip=None, notes=None):
    """Create the profile for `name`, or change only the details given."""
    name = name.strip()
    if not name:
        raise ValidationError("Guest name is required")
    if email and "@" not in email:
        raise ValidationError(f"Not an email address: {email}")
    guest = hotel.guests.setdefault(name, Guest(name))
    if email is not None:
        guest.email = email
    if phone is not None:
        guest.phone = phone
    if vip is not None:
        guest.vip = vip
    if notes is not None:
        guest.notes = notes
    return guest


def find(hotel, text):
    """Profiles whose name contains `text`, ignoring case."""
    text = text.strip().lower()
    return sorted((guest for guest in hotel.guests.values() if text in guest.name.lower()),
                  key=lambda guest: guest.name)


def is_vip(hotel, name):
    guest = hotel.guests.get(name)
    return guest is not None and guest.vip


def stays(hotel, name):
    """Every reservation under the guest's name, earliest arrival first."""
    return sorted((r for r in hotel.reservations.values() if r.guest == name), key=lambda r: (r.arrival, r.id))


def history(hotel, name):
    """Stays completed or under way, with the nights and room revenue they brought."""
    stayed = [r for r in stays(hotel, name) if r.status in (IN_HOUSE, CHECKED_OUT)]
    return {
        "name": name,
        "stays": len(stayed),
        "nights": sum(r.nights for r in stayed),
        "room_revenue": sum(r.room_total for r in stayed),
        "last_arrival": stayed[-1].arrival if stayed else None,
    }
