"""Nightly rates for a stay, and the quote the desk reads out to the guest."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from .._generated import TAX_RATES
from ..dates import nights
from ..money import adjust
from .stay_rules import check_stay

# Friday and Saturday nights carry the weekend uplift.
WEEKEND_NIGHTS = (4, 5)


def nightly_rates(hotel, settings, room_type, plan_code, arrival, departure):
    """The rate for each night of the stay in cents, arrival night first."""
    base = hotel.room_type(room_type).base_rate
    plan = hotel.rate_plan(plan_code)
    rates = []
    for night in nights(arrival, departure):
        rate = adjust(base, settings.weekend_uplift_percent) if night.weekday() in WEEKEND_NIGHTS else base
        rates.append(adjust(rate, -plan.discount_percent))
    return rates


@dataclass
class Quote:
    room_type: str
    rate_plan: str
    arrival: date
    departure: date
    rates: list
    tax: int

    @property
    def room_total(self):
        return sum(self.rates)

    @property
    def total(self):
        return self.room_total + self.tax


def quote(hotel, settings, room_type, plan_code, arrival, departure, adults=1):
    check_stay(hotel, settings, room_type=room_type, arrival=arrival, departure=departure, adults=adults,
               rate_plan=plan_code)
    rates = nightly_rates(hotel, settings, room_type, plan_code, arrival, departure)
    # Each night is taxed on its own, the way the night audit posts it.
    lodging = TAX_RATES["lodging"]
    tax = sum(int(Decimal(rate) * lodging) for rate in rates)
    return Quote(room_type, plan_code, arrival, departure, rates, tax)
