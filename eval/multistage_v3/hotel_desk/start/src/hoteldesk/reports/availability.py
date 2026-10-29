"""Free rooms by type over the coming fortnight, for the reservations office."""
from datetime import timedelta

from ..services.inventory import availability
from .tables import table

DAYS = 14
COLUMNS = ("date", "type", "free")


def availability_rows(hotel, day):
    rows = []
    for code, counts in availability(hotel, day, DAYS).items():
        for offset, free in enumerate(counts):
            rows.append({"date": (day + timedelta(days=offset)).isoformat(), "type": code, "free": free})
    return sorted(rows, key=lambda row: (row["date"], row["type"]))


def availability_text(rows):
    """One line per date with a column for each room type, which reads better than the long list."""
    types = sorted({row["type"] for row in rows})
    dates = sorted({row["date"] for row in rows})
    free = {(row["date"], row["type"]): row["free"] for row in rows}
    body = table(("date",) + tuple(types), [[day] + [free[day, code] for code in types] for day in dates],
                 right=types)
    return f"Availability from {dates[0]}\n{body}"
