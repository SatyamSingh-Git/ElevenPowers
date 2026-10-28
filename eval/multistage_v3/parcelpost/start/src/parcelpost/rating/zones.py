"""Delivery zones, by postcode area, from the depot's zone chart."""
from .._generated import ZONE_CHART
from ..core.address import postcode_area
from ..core.errors import RatingError


def zone_for(postcode):
    area = postcode_area(postcode)
    try:
        return ZONE_CHART[area]
    except KeyError:
        raise RatingError(f"no service to postcode area {area}") from None


def areas_by_zone():
    zones = {}
    for area, zone in sorted(ZONE_CHART.items()):
        zones.setdefault(zone, []).append(area)
    return dict(sorted(zones.items()))
