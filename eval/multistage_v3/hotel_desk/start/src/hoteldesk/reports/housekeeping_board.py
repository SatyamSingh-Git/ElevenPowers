"""The housekeeping board: every room, its status and today's task."""
from ..services import housekeeping

COLUMNS = ("room", "floor", "type", "status", "occupied", "task")


def board_rows(hotel, day):
    # The board always shows the rooms as they are now; the day is accepted so every report reads alike.
    work = dict(housekeeping.tasks(hotel))
    return [
        {
            "room": room.number,
            "floor": room.floor,
            "type": room.type_code,
            "status": room.status,
            "occupied": "yes" if room.occupied else "no",
            "task": work.get(room.number, ""),
        }
        for room in sorted(hotel.rooms.values(), key=lambda room: (room.floor, room.number))
    ]


def board_summary(hotel):
    counts = housekeeping.status_counts(hotel)
    return "  ".join(f"{status}: {count}" for status, count in counts.items())
