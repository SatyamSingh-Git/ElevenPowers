"""Occupancy for the week ahead, from the business date or a chosen date."""
from datetime import timedelta

from ..money import format_money
from ..services.inventory import day_statistics
from .tables import table

COLUMNS = ("date", "rooms", "out_of_order", "available", "sold", "occupancy", "adr", "revpar")
DAYS = 7


def occupancy_rows(hotel, day):
    rows = []
    for offset in range(DAYS):
        stats = day_statistics(hotel, day + timedelta(days=offset))
        rows.append({
            "date": stats["date"],
            "rooms": stats["rooms"],
            "out_of_order": stats["out_of_order"],
            "available": stats["available"],
            "sold": stats["sold"],
            "occupancy": stats["occupancy"],
            "adr": format_money(stats["adr"]),
            "revpar": format_money(stats["revpar"]),
        })
    return rows


def occupancy_text(rows):
    shown = [{**row, "occupancy": f"{row['occupancy'] * 100:.1f}%"} for row in rows]
    body = table(COLUMNS, [[row[column] for column in COLUMNS] for row in shown],
                 right=("rooms", "out_of_order", "available", "sold", "occupancy", "adr", "revpar"))
    return f"Occupancy from {rows[0]['date']}\n{body}"
