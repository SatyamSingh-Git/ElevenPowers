"""A week at a glance: appointments per practitioner per day."""
from datetime import timedelta

from .textfmt import table


def week_days(any_day):
    monday = any_day - timedelta(days=any_day.weekday())
    return [monday + timedelta(days=offset) for offset in range(7)]


def week_grid(bookings, clinic, any_day):
    """For each practitioner, appointments per day of the week containing `any_day`.

    A day the practitioner does not work, or the clinic is shut, is None rather than 0.
    """
    days = week_days(any_day)
    grid = {}
    for practitioner in clinic.practitioners:
        counts = []
        for day in days:
            if practitioner not in clinic.working_on(day):
                counts.append(None)
                continue
            counts.append(sum(
                1 for booking in bookings
                if booking.practitioner == practitioner.id and booking.day == day and booking.active
            ))
        grid[practitioner.id] = counts
    return days, grid


def render_week(bookings, clinic, any_day):
    days, grid = week_grid(bookings, clinic, any_day)
    headers = ["practitioner"] + [f"{day:%a %d}" for day in days]
    rows = []
    for practitioner in clinic.practitioners:
        cells = ["-" if count is None else count for count in grid[practitioner.id]]
        rows.append([practitioner.name] + cells)
    return [f"Week of {days[0]:%d %B %Y}"] + table(headers, rows)
