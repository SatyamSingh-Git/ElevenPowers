"""Base postage from the rate card, by service, zone and billable weight."""
from .._generated import BASE_RATES, EXTRA_KG_PENCE, SERVICES
from ..core.errors import RatingError
from ..core.units import GRAMS_PER_KG, round_up

VOLUMETRIC_DIVISOR = 5000  # cubic centimetres per kilogram
WEIGHT_STEP_GRAMS = 500


def services():
    return list(SERVICES)


def check_service(service):
    if service not in SERVICES:
        raise RatingError(f"unknown service: {service}")
    return service


def service_name(service):
    return SERVICES[check_service(service)][0]


def transit_days(service):
    return SERVICES[check_service(service)][1]


def volumetric_grams(parcel):
    return round_up(parcel.volume_cm3 * GRAMS_PER_KG, VOLUMETRIC_DIVISOR) // VOLUMETRIC_DIVISOR


def billable_grams(parcel):
    """The greater of actual and volumetric weight, rounded up to the next weight step."""
    return round_up(max(parcel.weight_grams, volumetric_grams(parcel)), WEIGHT_STEP_GRAMS)


def base_rate(service, zone, grams):
    bands = BASE_RATES[check_service(service)]
    for limit, prices in bands:
        if grams <= limit:
            return prices[zone - 1]
    top_limit, top_prices = bands[-1]
    extra_kg = round_up(grams - top_limit, GRAMS_PER_KG) // GRAMS_PER_KG
    return top_prices[zone - 1] + extra_kg * EXTRA_KG_PENCE[service]
