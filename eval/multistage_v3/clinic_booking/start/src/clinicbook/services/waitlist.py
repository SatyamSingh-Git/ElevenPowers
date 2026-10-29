"""The waiting list: patients who want an earlier appointment than they could get.

When a slot frees up, reception looks at the offers and phones the patient
who has waited longest.
"""
from dataclasses import dataclass
from datetime import date, datetime

from ..errors import BookingError
from .availability import free_slots_from
from .validation import check_name, check_phone

ANY = "any"


@dataclass(frozen=True)
class WaitEntry:
    patient: str
    phone: str
    practitioner: str
    earliest: date
    latest: date
    added: datetime

    def accepts(self, slot):
        if self.practitioner != ANY and slot.practitioner != self.practitioner:
            return False
        return self.earliest <= slot.day <= self.latest


@dataclass(frozen=True)
class Offer:
    entry: WaitEntry
    slot: object


def new_entry(clinic, patient, phone, practitioner, earliest, latest, now):
    """A checked waiting-list entry; `practitioner` may be `any`."""
    if practitioner != ANY:
        clinic.practitioner(practitioner)
    if latest < earliest:
        raise BookingError("the latest day is before the earliest day")
    if latest < now.date():
        raise BookingError("the latest day has already passed")
    return WaitEntry(check_name(patient), check_phone(phone), practitioner, earliest, latest, now)


def add(waitlist, entry):
    """Add `entry`, unless the same phone already waits for the same practitioner."""
    for waiting in waitlist:
        if waiting.phone == entry.phone and waiting.practitioner == entry.practitioner:
            raise BookingError(f"{entry.phone} is already waiting for {entry.practitioner}")
    waitlist.append(entry)
    return entry


def remove(waitlist, phone):
    """Drop every entry for `phone`; returns how many there were."""
    phone = check_phone(phone)
    kept = [entry for entry in waitlist if entry.phone != phone]
    removed = len(waitlist) - len(kept)
    waitlist[:] = kept
    return removed


def expired(waitlist, today):
    return [entry for entry in waitlist if entry.latest < today]


def offers(waitlist, clinic, bookings, now):
    """Pair waiting patients with free slots, longest-waiting first.

    Each patient is offered at most one slot and each slot goes to at most one
    patient, so the list can be worked through on the phone from the top.
    """
    queue = sorted((entry for entry in waitlist if entry.latest >= now.date()), key=lambda e: e.added)
    if not queue:
        return []
    first = max(min(entry.earliest for entry in queue), now.date())
    last = max(entry.latest for entry in queue)
    slots = free_slots_from(clinic, bookings, first, (last - first).days + 1, now)
    taken = set()
    found = []
    for entry in queue:
        for slot in slots:
            key = (slot.practitioner, slot.day, slot.start)
            if key not in taken and entry.accepts(slot):
                taken.add(key)
                found.append(Offer(entry, slot))
                break
    return found
