"""Room revenue already on the books for the nights ahead."""
from datetime import timedelta

from ..model.reservations import HOLDING
from ..money import format_money
from .tables import table

COLUMNS = ("date", "rooms", "room_revenue", "arrivals", "departures")
DAYS = 30


def forecast_rows(hotel, day):
    rows = []
    for offset in range(DAYS):
        night = day + timedelta(days=offset)
        holding = [r for r in hotel.reservations.values() if r.status in HOLDING]
        staying = [r for r in holding if r.covers(night)]
        rows.append({
            "date": night.isoformat(),
            "rooms": len(staying),
            "room_revenue": format_money(sum(r.rate_for(night) for r in staying)),
            "arrivals": sum(1 for r in holding if r.arrival == night),
            "departures": sum(1 for r in holding if r.departure == night),
        })
    return rows


def forecast_text(rows):
    body = table(COLUMNS, [[row[column] for column in COLUMNS] for row in rows],
                 right=("rooms", "room_revenue", "arrivals", "departures"))
    return f"Forecast from {rows[0]['date']}\n{body}"
