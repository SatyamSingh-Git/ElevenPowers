"""Wall-clock times within one day, counted in minutes from midnight."""
from datetime import time


def parse_hhmm(text):
    """`09:30` as a time. Only two-digit hours and minutes are accepted."""
    parts = text.split(":")
    if len(parts) != 2 or not all(len(part) == 2 and part.isdigit() for part in parts):
        raise ValueError(f"not a time: {text!r}")
    hours, minutes = int(parts[0]), int(parts[1])
    if hours > 23 or minutes > 59:
        raise ValueError(f"not a time: {text!r}")
    return time(hours, minutes)


def minutes_of(moment):
    return moment.hour * 60 + moment.minute


def from_minutes(total):
    return time(total // 60, total % 60)


def add_minutes(moment, minutes):
    return from_minutes(minutes_of(moment) + minutes)


def minutes_between(start, end):
    return minutes_of(end) - minutes_of(start)
