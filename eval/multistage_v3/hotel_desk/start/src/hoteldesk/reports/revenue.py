"""Revenue over a run of closed days, read from the audit journal."""
import csv
from pathlib import Path

from ..dates import parse_date
from ..errors import NotFound
from ..money import format_money, per
from .tables import table

AMOUNTS = ("room_revenue", "tax_revenue", "other_revenue", "payments")


def revenue_summary(journal_path, start=None, end=None):
    """Totals for the closed days from `start` to `end`, both included; either may be left open."""
    path = Path(journal_path)
    if not path.is_file():
        raise NotFound(f"No audit journal at {path}")
    days = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            day = parse_date(row["business_date"])
            if (start and day < start) or (end and day > end):
                continue
            days.append({
                "date": day,
                "rooms_sold": int(row["rooms_sold"]),
                "rooms_available": int(row["rooms_available"]),
                **{name: int(row[name]) for name in AMOUNTS},
            })
    totals = {name: sum(day[name] for day in days) for name in ("rooms_sold", "rooms_available") + AMOUNTS}
    totals["adr"] = per(totals["room_revenue"], totals["rooms_sold"])
    totals["revpar"] = per(totals["room_revenue"], totals["rooms_available"])
    return {"days": days, "totals": totals}


def revenue_text(summary):
    days, totals = summary["days"], summary["totals"]
    if not days:
        return "No closed days in that range"
    columns = ("date", "sold", "room", "tax", "other", "payments")
    rows = [[day["date"].isoformat(), day["rooms_sold"], format_money(day["room_revenue"]),
             format_money(day["tax_revenue"]), format_money(day["other_revenue"]), format_money(day["payments"])]
            for day in days]
    rows.append(["total", totals["rooms_sold"], format_money(totals["room_revenue"]),
                 format_money(totals["tax_revenue"]), format_money(totals["other_revenue"]),
                 format_money(totals["payments"])])
    body = table(columns, rows, right=columns[1:])
    return (f"Revenue {days[0]['date'].isoformat()} to {days[-1]['date'].isoformat()}\n{body}\n"
            f"ADR {format_money(totals['adr'])}  RevPAR {format_money(totals['revpar'])}")
