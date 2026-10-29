"""Day reports the CLI prints by name, in text, JSON or CSV."""
import csv
from dataclasses import dataclass
import io
import json

from . import arrivals, availability, cashier, forecast, housekeeping_board, ledger, occupancy
from .tables import table


@dataclass(frozen=True)
class Report:
    title: str
    columns: tuple
    rows: object
    text: object = None


REPORTS = {
    "arrivals": Report("Arrivals", arrivals.ARRIVAL_COLUMNS, arrivals.arrival_rows),
    "departures": Report("Departures", arrivals.DEPARTURE_COLUMNS, arrivals.departure_rows),
    "inhouse": Report("In house", arrivals.IN_HOUSE_COLUMNS, arrivals.in_house_rows),
    "occupancy": Report("Occupancy", occupancy.COLUMNS, occupancy.occupancy_rows, occupancy.occupancy_text),
    "housekeeping": Report("Housekeeping", housekeeping_board.COLUMNS, housekeeping_board.board_rows),
    "availability": Report("Availability", availability.COLUMNS, availability.availability_rows,
                           availability.availability_text),
    "payments": Report("Payments", cashier.COLUMNS, cashier.cashier_rows),
    "forecast": Report("Forecast", forecast.COLUMNS, forecast.forecast_rows, forecast.forecast_text),
    "ledger": Report("Guest ledger", ledger.COLUMNS, ledger.ledger_rows),
}
FORMATS = ("text", "json", "csv")


def render_report(name, hotel, day, fmt="text"):
    report = REPORTS[name]
    rows = report.rows(hotel, day)
    if fmt == "json":
        return json.dumps(rows, indent=2)
    if fmt == "csv":
        out = io.StringIO()
        writer = csv.DictWriter(out, fieldnames=report.columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        return out.getvalue().rstrip("\n")
    if not rows:
        return f"{report.title} {day.isoformat()}: none"
    if report.text is not None:
        return report.text(rows)
    body = table(report.columns, [[row[column] for column in report.columns] for row in rows])
    return f"{report.title} {day.isoformat()}\n{body}"
