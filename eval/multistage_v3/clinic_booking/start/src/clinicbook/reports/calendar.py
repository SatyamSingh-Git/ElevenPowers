"""A practitioner's appointments as an iCalendar file, for the calendar on their phone.

Only patient names and rooms go into the file; phone numbers stay at the clinic.
"""
from pathlib import Path

STAMP = "%Y%m%dT%H%M%S"


def _escape(text):
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def calendar_lines(bookings, clinic, practitioner_id, first, last):
    """VCALENDAR lines for the practitioner's appointments from `first` to `last` inclusive."""
    who = clinic.practitioner(practitioner_id)
    chosen = sorted(
        (booking for booking in bookings
         if booking.practitioner == who.id and booking.active and first <= booking.day <= last),
        key=lambda booking: booking.starts_at,
    )
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:-//clinicbook//{_escape(clinic.name)}//EN"]
    for booking in chosen:
        stamp = booking.created or booking.starts_at
        lines += [
            "BEGIN:VEVENT",
            f"UID:{booking.id}@clinicbook",
            f"DTSTAMP:{stamp:{STAMP}}",
            f"DTSTART:{booking.starts_at:{STAMP}}",
            f"DTEND:{booking.ends_at:{STAMP}}",
            f"SUMMARY:{_escape(booking.patient)}",
            f"LOCATION:{_escape(clinic.room(booking.room).name)}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return lines


def write_calendar(lines, path):
    # The iCalendar format asks for CRLF line endings whatever the platform.
    Path(path).write_bytes(("\r\n".join(lines) + "\r\n").encode("utf-8"))
