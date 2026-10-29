"""Seat lists as staff type them: `A1 A2 A3`, or `A1-A3` for a run along one row."""
import re

SEAT = re.compile(r"([A-Z]{1,2})(\d+)")


def expand_seats(words):
    """Seat ids from words such as `A7` or `A7-A10`, in the order given.

    A range stays within one row and may run either way, so `B4-B2` is B4, B3, B2.
    Anything else is passed through unchanged for the venue to reject.
    """
    seats = []
    for word in words:
        first, sep, last = word.upper().partition("-")
        start, end = SEAT.fullmatch(first), SEAT.fullmatch(last)
        if not sep or start is None or end is None or start.group(1) != end.group(1):
            seats.append(word.upper())
            continue
        row, low, high = start.group(1), int(start.group(2)), int(end.group(2))
        step = 1 if high >= low else -1
        seats.extend(f"{row}{number}" for number in range(low, high + step, step))
    return seats


def compress_seats(seats):
    """The reverse of expand_seats for display: runs along a row become `A1-A4`."""
    parts = []
    run = []
    for seat in seats:
        match = SEAT.fullmatch(seat)
        if match is None:
            parts.extend(_run_text(run))
            parts.append(seat)
            run = []
            continue
        row, number = match.group(1), int(match.group(2))
        if run and (row != run[-1][0] or number != run[-1][1] + 1):
            parts.extend(_run_text(run))
            run = []
        run.append((row, number))
    parts.extend(_run_text(run))
    return " ".join(parts)


def _run_text(run):
    if not run:
        return []
    if len(run) < 3:
        return [f"{row}{number}" for row, number in run]
    return [f"{run[0][0]}{run[0][1]}-{run[-1][0]}{run[-1][1]}"]
