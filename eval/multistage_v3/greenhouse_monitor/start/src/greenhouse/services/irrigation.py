"""Irrigation suggestions from each zone's soil moisture.

A zone is watered when its driest soil probe is more than ``dry_margin``
points below the zone's target. Each missing point asks for
``minutes_per_point`` minutes, up to ``max_irrigation_minutes``.
"""
from math import ceil

from ..core.model import Suggestion

SOIL = "soil_moisture"


def zone_moisture(latest, zone_id):
    """The driest latest soil moisture value in the zone, or None without a probe."""
    values = [r.value for r in latest.values() if r.zone == zone_id and r.kind == SOIL]
    return min(values) if values else None


def suggest(layout, latest, settings):
    """One suggestion per zone that has a moisture target, in layout order."""
    return [
        _suggestion(zone, zone_moisture(latest, zone.id), settings)
        for zone in layout.zones()
        if zone.target_moisture is not None
    ]


def _suggestion(zone, moisture, settings):
    target = zone.target_moisture
    if moisture is None:
        return Suggestion(zone.id, 0, "no soil moisture reading")
    deficit = target - moisture
    if deficit <= settings.dry_margin:
        return Suggestion(zone.id, 0, f"moisture {moisture:.1f}% near target {target:.1f}%")
    minutes = min(ceil(deficit * settings.minutes_per_point), settings.max_irrigation_minutes)
    return Suggestion(zone.id, minutes, f"moisture {moisture:.1f}% below target {target:.1f}%")


def total_minutes(suggestions):
    return sum(suggestion.minutes for suggestion in suggestions)
