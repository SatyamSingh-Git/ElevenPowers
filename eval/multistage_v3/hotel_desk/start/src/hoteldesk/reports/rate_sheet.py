"""Tonight's rate for every room type under every rate plan, for the phones."""
from datetime import timedelta

from ..money import format_money
from ..services.pricing import nightly_rates
from .tables import table


def rate_sheet(hotel, settings, day):
    plans = sorted(hotel.rate_plans)
    rows = []
    for code in sorted(hotel.room_types):
        rates = [nightly_rates(hotel, settings, code, plan, day, day + timedelta(days=1))[0] for plan in plans]
        rows.append([code] + [format_money(rate) for rate in rates])
    body = table(["type"] + plans, rows, right=plans)
    return f"Rates for the night of {day.isoformat()}\n{body}"
