"""The evening handover note: what today's desk leaves for tomorrow's."""
from datetime import timedelta

from ..model.booking import BOOKED, NO_SHOW


def _next_open(clinic, day):
    return clinic.hours.next_open_day(day + timedelta(days=1))


def handover_lines(bookings, clinic, today, sent):
    """Patients to chase from today, and how tomorrow looks.

    `sent` holds the references already queued for a reminder, so the note can
    say who will not get one.
    """
    lines = [f"Handover for {today:%A %d %B}"]
    missed = sorted((b for b in bookings if b.day == today and b.status == NO_SHOW), key=lambda b: b.start)
    if missed:
        lines.append("Did not come today - please phone:")
        lines += [f"  {b.start:%H:%M}  {b.patient}  {b.phone}  [{b.id}]" for b in missed]
    unresolved = [b for b in bookings if b.day == today and b.status == BOOKED]
    if unresolved:
        lines.append(f"Still marked booked from today: {', '.join(b.id for b in unresolved)}")
    following = _next_open(clinic, today)
    if following is None:
        lines.append("The clinic has no open days ahead")
        return lines
    coming = sorted((b for b in bookings if b.day == following and b.status == BOOKED), key=lambda b: b.start)
    lines.append(f"Next open day {following:%A %d %B}: {len(coming)} appointments")
    for practitioner in clinic.practitioners:
        theirs = [b for b in coming if b.practitioner == practitioner.id]
        if theirs:
            lines.append(f"  {practitioner.name}: {len(theirs)}, first at {theirs[0].start:%H:%M}")
    unreminded = [b for b in coming if b.id not in sent]
    if unreminded:
        lines.append(f"No reminder queued yet for: {', '.join(b.id for b in unreminded)}")
    return lines
