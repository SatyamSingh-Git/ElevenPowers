"""Reads the plain-text seat map a venue is described in.

    venue The Playhouse
    section Stalls tier=A
    row A 1-12
    row B 1-14 W:13,14 C:12

`row` lines belong to the section above them. After the seat range come access
codes from the venue's access audit, each followed by the seat numbers it
applies to. A `#` starts a comment.
"""
from pathlib import Path
import re

from .._generated import ACCESSIBILITY_CODES
from ..errors import BoxOfficeError
from ..model.venue import Venue

ROW_NAME = re.compile(r"[A-Z]{1,2}")
RANGE = re.compile(r"(\d+)-(\d+)")
TIER = re.compile(r"tier=([A-Z])")
FLAG = re.compile(r"([A-Z]):(\d+(?:,\d+)*)")


def parse_seatmap(text):
    venue = None
    section = None
    for line_number, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        keyword, _, rest = line.partition(" ")
        rest = rest.strip()
        if keyword == "venue":
            if venue is not None:
                raise _problem(line_number, "venue named twice")
            if not rest:
                raise _problem(line_number, "venue needs a name")
            venue = Venue(rest)
        elif keyword == "section":
            if venue is None:
                raise _problem(line_number, "section before venue")
            section = _section(venue, rest, line_number)
        elif keyword == "row":
            if section is None:
                raise _problem(line_number, "row before any section")
            _row(venue, section, rest, line_number)
        else:
            raise _problem(line_number, f"unknown keyword {keyword}")
    if venue is None:
        raise _problem(0, "no venue line")
    if venue.capacity == 0:
        raise _problem(0, "no seats")
    return venue


def read_seatmap(path):
    return parse_seatmap(Path(path).read_text(encoding="utf-8"))


def _section(venue, rest, line_number):
    name, _, option = rest.rpartition(" ")
    tier = TIER.fullmatch(option)
    if not name or tier is None:
        raise _problem(line_number, "expected: section NAME tier=T")
    if venue.section(name) is not None:
        raise _problem(line_number, f"section {name} defined twice")
    return venue.add_section(name, tier.group(1))


def _row(venue, section, rest, line_number):
    parts = rest.split()
    if len(parts) < 2 or not ROW_NAME.fullmatch(parts[0]):
        raise _problem(line_number, "expected: row LETTER FIRST-LAST [CODE:N,N]")
    row = parts[0]
    if venue.has_row(row):
        raise _problem(line_number, f"row {row} defined twice")
    span = RANGE.fullmatch(parts[1])
    if span is None or not 1 <= int(span.group(1)) <= int(span.group(2)):
        raise _problem(line_number, f"bad seat range {parts[1]}")
    first, last = int(span.group(1)), int(span.group(2))
    flags = {}
    for part in parts[2:]:
        flag = FLAG.fullmatch(part)
        if flag is None or flag.group(1) not in ACCESSIBILITY_CODES:
            raise _problem(line_number, f"unknown access code {part}")
        for number in map(int, flag.group(2).split(",")):
            if not first <= number <= last:
                raise _problem(line_number, f"seat {row}{number} is outside the row")
            flags.setdefault(number, set()).add(flag.group(1))
    venue.add_row(section, row, range(first, last + 1), flags)


def _problem(line_number, problem):
    return BoxOfficeError("bad-seatmap", line=line_number, problem=problem)


def format_seatmap(venue):
    """Seat map text for `venue`, in the form parse_seatmap reads."""
    lines = [f"venue {venue.name}"]
    for section in venue.sections:
        lines.append(f"section {section.name} tier={section.tier}")
        for row, seats in section.rows.items():
            codes = {}
            for seat in seats:
                for flag in sorted(seat.flags):
                    codes.setdefault(flag, []).append(str(seat.number))
            extra = "".join(f" {flag}:{','.join(numbers)}" for flag, numbers in sorted(codes.items()))
            lines.append(f"row {row} {seats[0].number}-{seats[-1].number}{extra}")
    return "\n".join(lines) + "\n"
