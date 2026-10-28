"""Quotes: base postage, surcharges and the fuel levy for one parcel to one postcode."""
from ..core.charges import BASE, FUEL, Line, Quote
from ..core.money import percent_of
from .surcharges import Context, applicable
from .tariff import base_rate, billable_grams, check_service, services
from .zones import zone_for


def quote(parcel, postcode, service, *, fuel_percent, residential=False, signature=False):
    check_service(service)
    zone = zone_for(postcode)
    grams = billable_grams(parcel)
    lines = [Line(BASE, base_rate(service, zone, grams))]
    lines += applicable(Context(parcel, service, zone, residential, signature))
    # The fuel levy is a percentage of everything else on the quote.
    lines.append(Line(FUEL, percent_of(sum(line.pence for line in lines), fuel_percent)))
    return Quote(service, zone, grams, tuple(lines))


def quote_all(parcel, postcode, *, fuel_percent, residential=False, signature=False):
    """One quote per service, cheapest first."""
    quotes = [quote(parcel, postcode, service, fuel_percent=fuel_percent,
                    residential=residential, signature=signature)
              for service in services()]
    return sorted(quotes, key=lambda found: (found.total, found.service))
