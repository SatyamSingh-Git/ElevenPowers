"""The audit log: one line for every change the desk makes, for when a patient disputes a fee."""
from pathlib import Path

DEFAULT_NAME = "audit.log"


def log_line(moment, action, booking):
    return f"{moment:%Y-%m-%dT%H:%M} {action} {booking.id} {booking.day} {booking.start:%H:%M} {booking.phone}"


def record(path, moment, action, bookings):
    with Path(path).open("a", encoding="utf-8") as handle:
        for booking in bookings:
            handle.write(log_line(moment, action, booking) + "\n")


def history(path, booking_id):
    """Logged lines about one booking, oldest first."""
    path = Path(path)
    if not path.exists():
        return []
    found = []
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split(" ")
        if len(parts) > 2 and parts[2] == booking_id:
            found.append(line)
    return found
