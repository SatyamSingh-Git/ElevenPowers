"""One practitioner's day on a single sheet, with the gaps between patients shown."""
from ..model.times import minutes_between


def sheet_lines(bookings, clinic, practitioner_id, day):
    who = clinic.practitioner(practitioner_id)
    header = [f"{who.name} - {clinic.room(who.room).name} - {day:%A %d %B %Y}"]
    window = clinic.hours.window(day)
    if window is None:
        return header + [f"Clinic closed: {clinic.hours.closed_reason(day)}"]
    if not who.works_on(day):
        return header + ["Not working today"]
    theirs = sorted(
        (b for b in bookings if b.practitioner == who.id and b.day == day and b.active),
        key=lambda b: b.start,
    )
    opens, closes = window
    lines = list(header)
    cursor = opens
    for booking in theirs:
        gap = minutes_between(cursor, booking.start)
        if gap > 0:
            lines.append(f"{cursor:%H:%M}  ({gap} min free)")
        lines.append(f"{booking.start:%H:%M}  {booking.patient}  {booking.phone}  [{booking.id}]")
        cursor = max(cursor, booking.end)
    tail = minutes_between(cursor, closes)
    if tail > 0:
        lines.append(f"{cursor:%H:%M}  ({tail} min free)")
    lines.append(f"{len(theirs)} patients")
    return lines
