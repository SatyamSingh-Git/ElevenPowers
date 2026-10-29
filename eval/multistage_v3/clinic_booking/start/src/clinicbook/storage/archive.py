"""Old bookings moved out of the bookings file into one archive file per year.

Archives use the bookings file's own format, so every command that takes
`--bookings` can be pointed at one to look back at a past year.
"""
from pathlib import Path

from .bookings_file import load_bookings, save_bookings


def archive_path(path, year):
    path = Path(path)
    return path.with_name(f"{path.stem}-{year}{path.suffix}")


def split_before(bookings, cutoff):
    """(kept, old): bookings on or after `cutoff`, and those before it."""
    kept = [booking for booking in bookings if booking.day >= cutoff]
    old = [booking for booking in bookings if booking.day < cutoff]
    return kept, old


def archive_before(path, cutoff):
    """Move bookings before `cutoff` into the yearly archives; returns how many moved."""
    kept, old = split_before(load_bookings(path), cutoff)
    if not old:
        return 0
    for year in sorted({booking.day.year for booking in old}):
        target = archive_path(path, year)
        existing = load_bookings(target)
        known = {booking.id for booking in existing}
        moving = [booking for booking in old if booking.day.year == year and booking.id not in known]
        save_bookings(existing + moving, target)
    save_bookings(kept, path)
    return len(old)
