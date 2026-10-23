from decimal import Decimal

from .money import quantize


class TaxError(ValueError):
    pass


# region: category: [(date the rate took effect, percent), ...] in date order.
RATES = {
    "US-NY": {
        "standard": [("2009-08-01", "8.875")],
        "food": [("2009-08-01", "0")],
        "books": [("2009-08-01", "8.875")],
        "digital": [("2009-08-01", "8.875")],
        "services": [("2009-08-01", "0")],
    },
    "DE": {
        "standard": [("2021-01-01", "19")],
        "food": [("2021-01-01", "7")],
        "books": [("2021-01-01", "7")],
        "digital": [("2021-01-01", "19")],
        "services": [("2021-01-01", "19")],
    },
    "GB": {
        "standard": [("2011-01-04", "20")],
        "food": [("2011-01-04", "20")],
        "books": [("2011-01-04", "20")],
        "digital": [("2011-01-04", "20")],
        "services": [("2011-01-04", "20")],
    },
    "JP": {
        "standard": [("2019-10-01", "10")],
        "food": [("2019-10-01", "8")],
        "books": [("2019-10-01", "10")],
        "digital": [("2019-10-01", "10")],
        "services": [("2019-10-01", "10")],
    },
    "IN": {
        "standard": [("2017-07-01", "18")],
        "food": [("2017-07-01", "5")],
        "books": [("2017-07-01", "0")],
        "digital": [("2017-07-01", "18")],
        "services": [("2017-07-01", "18")],
    },
}


def normalize_region(code):
    region = str(code).strip().upper()
    if region not in RATES:
        raise TaxError(f"unknown region: {code}")
    return region


def rate_for(category, region):
    """Percent charged on `category` in `region`: the latest rate listed."""
    history = RATES[normalize_region(region)][category]
    return Decimal(history[-1][1])


def format_rate(rate):
    return f"{rate.normalize():f}%"


def line_tax(net, category, region, currency, rounding):
    return quantize(net * rate_for(category, region) / 100, currency, rounding)
