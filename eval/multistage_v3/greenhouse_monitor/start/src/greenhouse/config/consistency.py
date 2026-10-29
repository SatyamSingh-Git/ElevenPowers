"""Cross-checks between configuration files that each load fine on their own."""
from .crops import CROPS


def problems(layout, thresholds, offsets, settings):
    """Every inconsistency found, as sentences, in a stable order."""
    found = []
    for zone in thresholds.zones():
        if zone not in layout:
            found.append(f"thresholds name unknown zone {zone}")
    valves = {}
    for zone in layout.zones():
        if zone.crop not in CROPS:
            found.append(f"zone {zone.id} grows unknown crop {zone.crop}")
        if zone.valve in valves:
            found.append(f"zones {valves[zone.valve]} and {zone.id} share valve {zone.valve}")
        valves.setdefault(zone.valve, zone.id)
    for sensor, offset in offsets:
        if abs(offset) > settings.max_offset:
            found.append(f"offset for {sensor} is beyond max_offset {settings.max_offset}")
    if settings.vpd_low_kpa >= settings.vpd_high_kpa:
        found.append("vpd_low_kpa must be below vpd_high_kpa")
    return found
