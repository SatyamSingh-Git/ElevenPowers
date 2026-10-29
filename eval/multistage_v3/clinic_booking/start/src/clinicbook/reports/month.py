"""A month on one page: appointments booked on each day, closed days marked."""
import calendar
from datetime import date


def month_counts(bookings, clinic, year, month):
    """{day: number of active bookings}, with None for days the clinic is shut."""
    counts = {}
    for number in range(1, calendar.monthrange(year, month)[1] + 1):
        day = date(year, month, number)
        if clinic.hours.window(day) is None:
            counts[day] = None
            continue
        counts[day] = sum(1 for booking in bookings if booking.day == day and booking.active)
    return counts


def render_month(bookings, clinic, year, month):
    """A calendar grid, Monday first; each cell is the day and its count, or `--` when shut."""
    counts = month_counts(bookings, clinic, year, month)
    lines = [f"{calendar.month_name[month]} {year}", "  ".join(f"{name:>6}" for name in calendar.day_abbr)]
    for week in calendar.Calendar().monthdatescalendar(year, month):
        cells = []
        for day in week:
            if day.month != month:
                cells.append(" " * 6)
            elif counts[day] is None:
                cells.append(f"{day.day:>2} --")
            else:
                cells.append(f"{day.day:>2} {counts[day]:>3}")
        lines.append("  ".join(f"{cell:>6}" for cell in cells).rstrip())
    return lines
