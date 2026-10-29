"""Room status for housekeeping, and the day's cleaning list."""
from ..errors import InvalidState, ValidationError
from ..model.reservations import IN_HOUSE
from ..model.rooms import CLEAN, DIRTY, HOUSEKEEPING_STATUSES, OUT_OF_ORDER

# Tasks in the order a room attendant works them.
TASKS = ("departure clean", "clean", "stayover", "inspect")


def set_status(hotel, room_number, status):
    if status not in HOUSEKEEPING_STATUSES:
        raise ValidationError(f"Unknown housekeeping status: {status}")
    room = hotel.room(room_number)
    if status == OUT_OF_ORDER and room.occupied:
        raise InvalidState(f"Room {room.number} is occupied")
    room.status = status
    return room


def due_out(hotel):
    """Rooms whose guests leave on the business date."""
    return sorted(r.room for r in hotel.reservations_with(IN_HOUSE) if r.departure == hotel.business_date)


def tasks(hotel):
    """(room number, task) pairs for every room that needs housekeeping today."""
    leaving = set(due_out(hotel))
    work = []
    for room in hotel.rooms.values():
        if room.number in leaving:
            work.append((room.number, "departure clean"))
        elif room.occupied:
            work.append((room.number, "stayover"))
        elif room.status == DIRTY:
            work.append((room.number, "clean"))
        elif room.status == CLEAN:
            work.append((room.number, "inspect"))
    return sorted(work, key=lambda item: (TASKS.index(item[1]), item[0]))


def assign(hotel, attendants):
    """Share today's tasks among the attendants floor by floor, so nobody crosses floors more than needed.

    Returns {attendant: [(room number, task), ...]}.
    """
    if not attendants:
        raise ValidationError("Name at least one attendant")
    sheets = {}
    by_floor = sorted(tasks(hotel), key=lambda item: (hotel.room(item[0]).floor, item[0]))
    share, extra = divmod(len(by_floor), len(attendants))
    start = 0
    for position, name in enumerate(attendants):
        count = share + (1 if position < extra else 0)
        sheets[name] = by_floor[start:start + count]
        start += count
    return sheets


def status_counts(hotel):
    counts = dict.fromkeys(HOUSEKEEPING_STATUSES, 0)
    for room in hotel.rooms.values():
        counts[room.status] += 1
    return counts
